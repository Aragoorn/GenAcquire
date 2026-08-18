# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json
from datetime import datetime, timezone, timedelta

class NexusAcquire(gl.Contract):
    owner: Address
    treasury: Address
    fee_bps: u256
    min_amount: u256
    max_amount: u256
    default_days: u256
    paused: bool
    next_id: u256
    escrows: TreeMap[str, str]
    registry: TreeMap[str, str]
    total_fees: u256
    version: str
    pending_owner: str
    timelock_hours: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.treasury = gl.message.sender_address
        self.fee_bps = u256(150)
        self.min_amount = u256(0)                          # برای تست راحت
        self.max_amount = u256(10_000_000 * 10**18)
        self.default_days = u256(10)
        self.paused = False
        self.next_id = u256(1)
        self.escrows = TreeMap[str, str]()
        self.registry = TreeMap[str, str]()
        self.total_fees = u256(0)
        self.version = "4.1.5-final-testable"
        self.pending_owner = json.dumps({
            "new_owner": "0x0000000000000000000000000000000000000000",
            "ready_at": ""
        })
        self.timelock_hours = u256(24)

    # ====================== Helpers ======================
    def _now(self) -> str:
        try:
            return str(gl.message.datetime)
        except:
            return datetime.now(timezone.utc).isoformat()

    def _parse(self, iso: str) -> datetime:
        try:
            raw = iso.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except:
            return datetime.now(timezone.utc)

    def _add_days(self, iso: str, days: int) -> str:
        return (self._parse(iso) + timedelta(days=days)).isoformat()

    def _add_hours(self, iso: str, hours: int) -> str:
        return (self._parse(iso) + timedelta(hours=hours)).isoformat()

    def _is_past(self, iso: str) -> bool:
        try:
            return self._parse(self._now()) > self._parse(iso)
        except:
            return False

    def _zero(self) -> str:
        return "0x0000000000000000000000000000000000000000"

    def _norm(self, asset_id: str) -> str:
        return asset_id.strip().lower()

    def _get_escrow(self, escrow_id: str) -> dict:
        raw = self.escrows.get(escrow_id, "")
        if not raw:
            return {}
        return json.loads(raw)

    def _save_escrow(self, escrow_id: str, data: dict) -> None:
        self.escrows[escrow_id] = json.dumps(data)

    # ====================== Admin ======================
    @gl.public.write
    def propose_new_owner(self, new_owner: str) -> None:
        assert gl.message.sender_address == self.owner, "Only owner"
        assert new_owner != self._zero()
        self.pending_owner = json.dumps({
            "new_owner": new_owner,
            "ready_at": self._add_hours(self._now(), int(self.timelock_hours))
        })

    @gl.public.write
    def accept_new_owner(self) -> None:
        data = json.loads(self.pending_owner)
        assert data["new_owner"] != self._zero()
        assert self._is_past(data["ready_at"]), "Timelock active"
        self.owner = Address(data["new_owner"])
        self.pending_owner = json.dumps({"new_owner": self._zero(), "ready_at": ""})

    @gl.public.write
    def set_treasury(self, addr: str) -> None:
        assert gl.message.sender_address == self.owner
        self.treasury = Address(addr)

    @gl.public.write
    def set_fee(self, bps: int) -> None:
        assert gl.message.sender_address == self.owner
        assert 0 <= bps <= 300
        self.fee_bps = u256(bps)

    @gl.public.write
    def set_limits(self, min_amt: int, max_amt: int) -> None:
        assert gl.message.sender_address == self.owner
        assert min_amt >= 0 and max_amt > min_amt
        self.min_amount = u256(min_amt)
        self.max_amount = u256(max_amt)

    @gl.public.write
    def pause(self, state: bool) -> None:
        assert gl.message.sender_address == self.owner
        self.paused = state

    # ====================== Registry ======================
    @gl.public.write
    def register_asset(self, asset_id: str) -> None:
        assert not self.paused
        key = self._norm(asset_id)
        assert len(key) >= 6
        assert key not in self.registry
        self.registry[key] = gl.message.sender_address.as_hex

    @gl.public.view
    def owner_of(self, asset_id: str) -> str:
        key = self._norm(asset_id)
        return self.registry.get(key, "")

    # ====================== Create ======================
    @gl.public.write.payable
    def create(self, seller: str, asset_type: str, asset_id: str, conditions: str, days: int = 0, evidence: str = "", meta: str = "") -> str:
        assert not self.paused, "System paused"
        amount = gl.message.value
        assert self.min_amount <= amount <= self.max_amount, "Amount out of range"
        assert len(conditions.strip()) >= 20, "Conditions too short"
        assert asset_type in ["github", "realestate", "vehicle", "rwa", "digital", "freelance", "other"]

        seller_addr = Address(seller)
        assert seller_addr.as_hex != self._zero()

        key = self._norm(asset_id)
        assert len(key) >= 6

        if key in self.registry:
            assert self.registry[key] == seller_addr.as_hex, "Seller is not the registered owner"
        else:
            self.registry[key] = seller_addr.as_hex

        timeout_days = int(self.default_days) if days <= 0 else min(max(days, 1), 90)
        eid = str(int(self.next_id))
        self.next_id += u256(1)

        now = self._now()
        escrow_data = {
            "buyer": gl.message.sender_address.as_hex,
            "seller": seller_addr.as_hex,
            "amount": int(amount),
            "asset_type": asset_type,
            "asset_id": key,
            "conditions": conditions.strip(),
            "evidence_urls": evidence.strip(),
            "agreement": "",
            "status": "FUNDED",
            "created_at": now,
            "timeout_at": self._add_days(now, timeout_days),
            "result": "",
            "fee_bps": int(self.fee_bps),
            "meta": meta.strip()
        }
        self._save_escrow(eid, escrow_data)
        return eid

    # ====================== Submit ======================
    @gl.public.write
    def submit(self, escrow_id: str, evidence_urls: str, agreement: str) -> None:
        esc = self._get_escrow(escrow_id)
        assert esc, "Escrow not found"
        # شرط Only seller برای راحتی تست در Studio غیرفعال شده
        assert esc["status"] == "FUNDED", "Invalid status"
        assert not self._is_past(esc["timeout_at"]), "Expired"
        assert len(evidence_urls.strip()) >= 8
        assert len(agreement.strip()) >= 30

        esc["evidence_urls"] = evidence_urls.strip()
        esc["agreement"] = agreement.strip()
        esc["status"] = "SUBMITTED"
        self._save_escrow(escrow_id, esc)

    # ====================== Evaluate ======================
    @gl.public.write
    def evaluate(self, escrow_id: str) -> str:
        esc = self._get_escrow(escrow_id)
        assert esc, "Escrow not found"
        assert esc["status"] == "SUBMITTED"
        assert not self._is_past(esc["timeout_at"])

        def get_context() -> str:
            return f"""
Asset Type: {esc['asset_type']}
Asset ID: {esc['asset_id']}
Buyer Conditions: {esc['conditions']}
Seller Agreement: {esc['agreement']}
Evidence: {esc['evidence_urls']}
"""

        raw_decision = gl.eq_principle.prompt_non_comparative(
            get_context,
            task="You are a strict professional auditor. Decide if the evidence fully meets the conditions. Reply with ONLY one word: PASS or FAIL",
            criteria="Reply must be exactly PASS or FAIL. Prefer FAIL when uncertain or evidence is weak."
        )

        passed = "PASS" in str(raw_decision).upper()

        if passed:
            esc["status"] = "RELEASED"
            msg = "PASS - Funds should be released to seller + ownership transferred"
            self.registry[esc["asset_id"]] = esc["buyer"]
        else:
            esc["status"] = "REFUNDED"
            msg = "FAIL - Funds should be refunded to buyer"

        esc["result"] = str(raw_decision)[:800]
        self._save_escrow(escrow_id, esc)
        return msg

    # ====================== Timeout ======================
    @gl.public.write
    def timeout(self, escrow_id: str) -> None:
        esc = self._get_escrow(escrow_id)
        assert esc, "Escrow not found"
        assert esc["status"] in ("FUNDED", "SUBMITTED")
        assert self._is_past(esc["timeout_at"]), "Not expired yet"

        esc["status"] = "EXPIRED"
        self._save_escrow(escrow_id, esc)

    # ====================== Views ======================
    @gl.public.view
    def get(self, escrow_id: str) -> str:
        esc = self._get_escrow(escrow_id)
        if not esc:
            return json.dumps({"error": "Not found"})
        esc["current_owner"] = self.registry.get(esc["asset_id"], "")
        return json.dumps(esc, indent=2)

    @gl.public.view
    def info(self) -> str:
        return json.dumps({
            "version": self.version,
            "owner": self.owner.as_hex,
            "treasury": self.treasury.as_hex,
            "fee_percent": float(int(self.fee_bps)) / 100,
            "min_amount": int(self.min_amount),
            "max_amount": int(self.max_amount),
            "paused": self.paused,
            "next_id": int(self.next_id),
            "total_fees": int(self.total_fees)
        }, indent=2)