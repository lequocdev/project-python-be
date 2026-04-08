from app.schemas.matching import Shipper, MatchingRequest, MatchingResponse, RankedShipper

# Trọng số cho từng yếu tố
WEIGHTS = {
    "distance": 0.40,
    "rating": 0.35,
    "acceptance_rate": 0.25,
}


def score_shipper(shipper: Shipper) -> float:
    """Tính điểm tổng cho một shipper (normalize về 0–1 trước khi nhân trọng số)."""
    distance_score = 1 / (1 + shipper.distance_km)          # gần hơn → điểm cao hơn
    rating_score = (shipper.rating - 1) / 4                  # scale 1–5 về 0–1
    acceptance_score = shipper.acceptance_rate                # đã là 0–1

    return (
        distance_score * WEIGHTS["distance"]
        + rating_score * WEIGHTS["rating"]
        + acceptance_score * WEIGHTS["acceptance_rate"]
    )


def rank_shippers(req: MatchingRequest) -> MatchingResponse:
    """Xếp hạng danh sách shippers và trả về kết quả."""
    scored = sorted(
        req.available_shippers,
        key=score_shipper,
        reverse=True,  # điểm cao → rank 1
    )

    ranked = [
        RankedShipper(
            shipper_id=s.shipper_id,
            score=round(score_shipper(s), 4),
            rank=idx + 1,
        )
        for idx, s in enumerate(scored)
    ]

    return MatchingResponse(
        order_id=req.order_id,
        ranked_shippers=ranked,
        top_shipper_id=ranked[0].shipper_id if ranked else "",
    )
