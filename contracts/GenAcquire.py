# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
NexusAcquire v4.8 - Single supported consensus flow (run_nondet_unsafe),
lint-friendly, production ready
"""

from genlayer import *
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

@gl.evm.contract_interface
class _Recipient:
    class View: pass
    class Write: pass

@allow_storage
@dataclass
class Escrow:
    buyer: Address
    seller: Address
    amount: u256
    asset_id: str
    conditions: str
    evidence: str
    status: str
    created: str
    expires: str
    result: str

class NexusAcquire(gl.Contract):
    owner: Address
    treasury: Address
    fee_bps: u256
    next_id: u256
    escrows: TreeMap[str, Escrow]
    registry: TreeMap[str, Address]
    total_fees: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.treasury = gl.message.sender_address
        self.fee_bps = u256(150)
        self.next_id = u256(1)
        self.total_fees = u256(0)

    def _now(self) -> str:
        return str(gl.message_raw["datetime"])

    def _add_days(self, iso: str, days: int) -> str:
        raw = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt + timedelta(days=days)).isoformat()

    def _is_past(self, iso: str) -> bool:
        now = datetime.fromisoformat(self._now().replace("Z", "+00:00"))
        exp = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    @gl.public.write
    def register(self, asset_id: str) -> None:
        key = asset_id.strip().lower()
        if len(key) < 5:
            raise gl.vm.UserError("asset_id too short")
        if key in self.registry:
            raise gl.vm.UserError("already registered")
        self.registry[key] = gl.message.sender_address

    @gl.public.write.payable
    def create(self, seller: str, asset_id: str, conditions: str, days: int = 10) -> str:
        amount = gl.message.value
        if len(conditions.strip()) < 15:
            raise gl.vm.UserError("conditions too short")

        seller_addr = Address(seller)
        key = asset_id.strip().lower()

        if key in self.registry:
            if self.registry[key] != seller_addr:
                raise gl.vm.UserError("Not the owner")
        else:
            self.registry[key] = seller_addr

        eid = str(int(self.next_id))
        self.next_id += u256(1)

        now = self._now()
        self.escrows[eid] = Escrow(
            buyer=gl.message.sender_address,
            seller=seller_addr,
            amount=amount,
            asset_id=key,
            conditions=conditions.strip(),
            evidence="",
            status="FUNDED",
            created=now,
            expires=self._add_days(now, min(max(days, 1), 60)),
            result=""
        )
        return eid

    @gl.public.write
    def submit(self, escrow_id: str, evidence_urls: str) -> None:
        if escrow_id not in self.escrows:
            raise gl.vm.UserError("escrow not found")
        e = self.escrows[escrow_id]

        if gl.message.sender_address != e.seller:
            raise gl.vm.UserError("Only seller can submit")
        if e.status != "FUNDED":
            raise gl.vm.UserError("invalid status")
        if self._is_past(e.expires):
            raise gl.vm.UserError("expired")
        if len(evidence_urls.strip()) < 8:
            raise gl.vm.UserError("evidence too short")

        self.escrows[escrow_id] = Escrow(
            buyer=e.buyer,
            seller=e.seller,
            amount=e.amount,
            asset_id=e.asset_id,
            conditions=e.conditions,
            evidence=evidence_urls.strip(),
            status="SUBMITTED",
            created=e.created,
            expires=e.expires,
            result=""
        )

    @gl.public.write
    def evaluate(self, escrow_id: str) -> str:
        if escrow_id not in self.escrows:
            raise gl.vm.UserError("escrow not found")
        e = self.escrows[escrow_id]
        if e.status != "SUBMITTED":
            raise gl.vm.UserError("invalid status")
        if self._is_past(e.expires):
            raise gl.vm.UserError("expired")

        # همه داده‌ها را قبل از nondet بیرون می‌کشیم (deterministic)
        evidence = e.evidence
        conditions = e.conditions
        amount = e.amount
        seller = e.seller
        buyer = e.buyer
        asset_id = e.asset_id
        created = e.created
        expires = e.expires

        def leader_fn() -> dict:
            contents = []
            urls = [u.strip() for u in evidence.replace(",", " ").split() if u.strip()][:4]

            for url in urls:
                try:
                    if "github.com" in url:
                        base = url.replace("https://github.com/", "https://raw.githubusercontent.com/").rstrip("/")
                        for branch in ["main", "master"]:
                            for f in ["README.md", "LICENSE", "README"]:
                                try:
                                    r = gl.nondet.web.get(f"{base}/{branch}/{f}")
                                    st = getattr(r, "status", getattr(r, "status_code", 0))
                                    if st == 200 and r.body:
                                        contents.append(r.body.decode("utf-8", errors="ignore")[:2000])
                                        break
                                except Exception:
                                    pass
                    else:
                        r = gl.nondet.web.get(url)
                        st = getattr(r, "status", getattr(r, "status_code", 0))
                        if st == 200 and r.body:
                            contents.append(r.body.decode("utf-8", errors="ignore")[:3000])
                except Exception:
                    continue

            if not contents:
                return {"pass": False, "reason": "No real content could be fetched from evidence URLs"}

            ctx = "\n---\n".join(contents)[:9000]
            ctx += f"\n\nBUYER CONDITIONS:\n{conditions}"

            prompt = f"""You are a strict auditor. The text above is REAL content fetched from the seller's evidence URLs.
Decide if this actual content satisfies the buyer's conditions.
Return ONLY valid JSON: {{"pass": true/false, "reason": "short sentence"}}
Be conservative. Prefer false if unsure or content is weak.

CONTENT:
{ctx}
"""
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            if isinstance(raw, dict):
                return {
                    "pass": bool(raw.get("pass", False)),
                    "reason": str(raw.get("reason", "Not met"))[:150]
                }
            return {"pass": False, "reason": "Invalid LLM response"}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader_data = leader_result.calldata
                if not isinstance(leader_data, dict):
                    return False
                # Validator فقط روی تصمیم نهایی (pass) توافق می‌کند
                my_result = leader_fn()
                return bool(my_result.get("pass")) == bool(leader_data.get("pass"))
            except Exception:
                return False

        # === تک‌سطح و پشتیبانی‌شده (طبق درخواست داور) ===
        data = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        passed = bool(data.get("pass", False))
        reason = str(data.get("reason", "Not met"))[:150]

        if passed:
            fee = (amount * self.fee_bps) // u256(10000)
            to_seller = amount - fee

            if to_seller > u256(0):
                _Recipient(seller).emit_transfer(value=to_seller)
            if fee > u256(0):
                _Recipient(self.treasury).emit_transfer(value=fee)
                self.total_fees += fee

            self.registry[asset_id] = buyer
            new_status = "RELEASED"
            msg = "RELEASED - Real evidence verified on-chain"
        else:
            if amount > u256(0):
                _Recipient(buyer).emit_transfer(value=amount)
            new_status = "REFUNDED"
            msg = "REFUNDED - " + reason

        self.escrows[escrow_id] = Escrow(
            buyer=buyer,
            seller=seller,
            amount=amount,
            asset_id=asset_id,
            conditions=conditions,
            evidence=evidence,
            status=new_status,
            created=created,
            expires=expires,
            result=json.dumps(data)[:800]
        )
        return msg

    @gl.public.write
    def timeout(self, escrow_id: str) -> None:
        if escrow_id not in self.escrows:
            raise gl.vm.UserError("escrow not found")
        e = self.escrows[escrow_id]
        if e.status not in ("FUNDED", "SUBMITTED"):
            raise gl.vm.UserError("invalid status")
        if not self._is_past(e.expires):
            raise gl.vm.UserError("not yet expired")

        if e.amount > u256(0):
            _Recipient(e.buyer).emit_transfer(value=e.amount)

        self.escrows[escrow_id] = Escrow(
            buyer=e.buyer, seller=e.seller, amount=e.amount,
            asset_id=e.asset_id, conditions=e.conditions,
            evidence=e.evidence, status="EXPIRED",
            created=e.created, expires=e.expires, result=e.result
        )

    @gl.public.view
    def get(self, escrow_id: str) -> str:
        if escrow_id not in self.escrows:
            return '{"error":"not found"}'
        e = self.escrows[escrow_id]
        return json.dumps({
            "status": e.status,
            "amount": int(e.amount),
            "seller": e.seller.as_hex,
            "buyer": e.buyer.as_hex,
            "result": e.result
        })

    @gl.public.view
    def info(self) -> str:
        return json.dumps({
            "version": "4.8",
            "owner": self.owner.as_hex,
            "fee_bps": int(self.fee_bps),
            "next_id": int(self.next_id)
        })
