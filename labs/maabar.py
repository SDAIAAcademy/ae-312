"""Maabar: a small model of a model gateway, for the AE-312 labs.

It does what the budget and limit features of a real gateway do, on replayed log rows instead
of live traffic: it attributes each request to a key, an application, an environment and a team,
adds up spend per budget and per window, raises a soft alert, refuses requests once a hard
budget is spent, and enforces a tokens-per-minute limit. Real gateways (LiteLLM is one example)
keep the same state in a database; this one keeps it in memory so a lab needs no server.

A policy is a dictionary:

    {"window": "day",
     "budgets": [{"scope": "app", "match": "fasil", "soft_sar": 120, "hard_sar": 150}],
     "rate_limits": [{"scope": "app", "match": "fasil", "tokens_per_minute": 400000}]}

scope is one of gateway, app, env, team, key; match is the value, or "*" for every value.
"""
from __future__ import annotations

from collections import deque

import pandas as pd

import mawj as M

SCOPES = ("gateway", "app", "env", "team", "key")


class Gateway:
    def __init__(self, policy):
        for b in policy.get("budgets", []) + policy.get("rate_limits", []):
            if b["scope"] not in SCOPES:
                raise ValueError(f"unknown scope {b['scope']!r}: use one of {SCOPES}")
        for b in policy.get("budgets", []):
            if b.get("soft_sar", 0) > b["hard_sar"]:
                raise ValueError("a soft budget above the hard budget never alerts in time")
        self.policy = policy
        self.events = []

    @staticmethod
    def attribute(df):
        """team, app and env of every row: the key register, with an app tag taking precedence."""
        out = M.with_register(df)
        tagged = M.tag(out, "app")
        out["app"] = tagged.where(tagged != "", out["app"])
        return out

    def _subjects(self, row, rule):
        value = {"gateway": "*", "app": row.app, "env": row.env, "team": row.team, "key": row.key_id}[rule["scope"]]
        if rule["match"] in ("*", value):
            return (rule["scope"], value)
        return None

    def replay(self, df):
        """Replay log rows in time order. Returns one row per request with the gateway's decision."""
        rows = M.add_cost(self.attribute(df)).sort_values("ts", kind="stable")
        spend, alerted, recent = {}, set(), {}
        self.events = []
        decisions, reasons = [], []
        for row in rows.itertuples(index=False):
            window = row.ts.strftime("%Y-%m-%d") if self.policy.get("window", "day") == "day" else row.ts.strftime("%Y-%m")
            refused = ""
            for rule in self.policy.get("budgets", []):
                subject = self._subjects(row, rule)
                if subject and spend.get((subject, window), 0.0) >= rule["hard_sar"]:
                    refused = f"budget_exceeded:{subject[0]}={subject[1]}"
                    break
            if not refused:
                for rule in self.policy.get("rate_limits", []):
                    subject = self._subjects(row, rule)
                    if subject:
                        q = recent.setdefault(subject, deque())
                        while q and (row.ts - q[0][0]).total_seconds() >= 60:
                            q.popleft()
                        if sum(n for _, n in q) + row.input_tokens > rule["tokens_per_minute"]:
                            refused = f"rate_limited:{subject[0]}={subject[1]}"
                            break
            if refused:
                decisions.append("refused")
                reasons.append(refused)
                continue
            decisions.append("allowed")
            reasons.append("")
            for rule in self.policy.get("rate_limits", []):
                subject = self._subjects(row, rule)
                if subject:
                    recent[subject].append((row.ts, row.input_tokens))
            for rule in self.policy.get("budgets", []):
                subject = self._subjects(row, rule)
                if not subject:
                    continue
                k = (subject, window)
                spend[k] = spend.get(k, 0.0) + row.cost_sar
                for level in ("soft_sar", "hard_sar"):
                    if level in rule and spend[k] >= rule[level] and (k, level) not in alerted:
                        alerted.add((k, level))
                        self.events.append({"ts": row.ts, "event": "soft_alert" if level == "soft_sar" else "hard_limit_reached",
                                            "scope": subject[0], "match": subject[1], "spend_sar": round(spend[k], 2), "limit_sar": rule[level]})
        rows["decision"], rows["reason"] = decisions, reasons
        rows["spent_sar"] = rows["cost_sar"].where(rows["decision"] == "allowed", 0.0)
        return rows

    def event_log(self):
        return pd.DataFrame(self.events, columns=["ts", "event", "scope", "match", "spend_sar", "limit_sar"])
