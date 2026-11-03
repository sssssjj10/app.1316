import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="장보기 알림메모",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------
# 스타일: 모바일 친화적이고 컴팩트한 단일 화면
# -------------------------
st.markdown("""
<style>
    .block-container {
        max-width: 900px;
        padding-top: 0.8rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    h1 { font-size: 1.55rem !important; margin-bottom: 0.2rem; }
    h2, h3 { font-size: 1.05rem !important; }
    div[data-testid="stMetric"] {
        background: #f3f8f2;
        border: 1px solid #dce9d9;
        padding: 0.5rem 0.7rem;
        border-radius: 0.7rem;
    }
    div[data-testid="stMetricValue"] { font-size: 1.25rem !important; }
    .item-card {
        background: #ffffff;
        border: 1px solid #e7e7e7;
        border-radius: 0.65rem;
        padding: 0.55rem 0.7rem;
        margin-bottom: 0.35rem;
    }
    .priority-1 { border-left: 5px solid #e05252; }
    .priority-2 { border-left: 5px solid #f0a33a; }
    .priority-3 { border-left: 5px solid #53a66b; }
    .small-note { color: #6b7280; font-size: 0.78rem; }
    button[kind="primary"] { border-radius: 0.6rem; }
    @media (max-width: 640px) {
        .block-container {
            padding-top: 0.35rem;
            padding-left: 0.65rem;
            padding-right: 0.65rem;
        }
        h1 { font-size: 1.3rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.05rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# 데이터 저장
# Streamlit Cloud 재시작 시에도 영구 보존이 필요하면 DB 사용 권장.
# 현재 코드는 세션 상태 기반으로 작동.
# -------------------------
if "items" not in st.session_state:
    st.session_state.items = []

if "memo" not in st.session_state:
    st.session_state.memo = ""

if "budget" not in st.session_state:
    st.session_state.budget = 30000

if "show_budget" not in st.session_state:
    st.session_state.show_budget = True

# -------------------------
# 제목
# -------------------------
st.title("🛒 장보기 알림메모")
st.caption("필요한 것만 담고, 가격과 수량을 기록해요.")

# -------------------------
# 예산 / 요약
# -------------------------
with st.expander("💰 예산 설정", expanded=False):
    st.session_state.show_budget = st.checkbox(
        "예산 표시하기",
        value=st.session_state.show_budget
    )
    if st.session_state.show_budget:
        st.session_state.budget = st.number_input(
            "장보기 예산 (원)",
            min_value=0,
            value=int(st.session_state.budget),
            step=1000
        )

purchased_items = [item for item in st.session_state.items if item["purchased"]]
total_cost = sum(item["price"] * item["quantity"] for item in purchased_items)
remaining_budget = st.session_state.budget - total_cost

if st.session_state.show_budget:
    m1, m2, m3 = st.columns(3)
    m1.metric("🧺 구매 총액", f"{total_cost:,}원")
    m2.metric("💳 예산", f"{st.session_state.budget:,}원")
    m3.metric("💵 남은 예산", f"{remaining_budget:,}원")
    if remaining_budget < 0:
        st.warning("예산을 초과했어요. 구매 목록을 확인해 보세요.")
else:
    st.metric("🧺 구매 총액", f"{total_cost:,}원")

# -------------------------
# 상품 추가
# -------------------------
st.subheader("➕ 장보기 목록 추가")

categories = [
    "🥬 채소", "🍎 과일", "🥩 육류", "🐟 해산물",
    "🥛 유제품", "🍞 빵·곡류", "🧂 조미료·양념",
    "🧻 생필품", "🧴 생활용품", "🍪 간식", "🥤 음료", "📦 기타"
]

with st.form("add_item_form", clear_on_submit=True):
    c1, c2 = st.columns([1, 2])
    category = c1.selectbox("카테고리", categories)
    product_name = c2.text_input("상품명", placeholder="예: 양파, 사과, 우유")

    c3, c4 = st.columns([1, 1])
    priority = c3.selectbox(
        "중요도",
        [1, 2, 3],
        format_func=lambda x: {1: "🔴 1 - 꼭 필요", 2: "🟠 2 - 가격 보고", 3: "🟢 3 - 선택"}[x]
    )
    note = c4.text_input("간단 메모 (선택)", placeholder="예: 작은 것 / 할인 상품")

    add_button = st.form_submit_button("목록에 추가", type="primary", use_container_width=True)

    if add_button:
        if product_name.strip():
            st.session_state.items.append({
                "id": f"{datetime.now().timestamp()}_{len(st.session_state.items)}",
                "category": category,
                "name": product_name.strip(),
                "priority": priority,
                "note": note.strip(),
                "purchased": False,
                "price": 0,
                "quantity": 1
            })
            st.success(f"'{product_name.strip()}' 상품을 추가했어요.")
            st.rerun()
        else:
            st.warning("상품명을 입력해 주세요.")

# -------------------------
# 목록 표시 및 구매 처리
# -------------------------
st.subheader("📝 살 물건")

not_purchased = [item for item in st.session_state.items if not item["purchased"]]
if not not_purchased:
    st.info("아직 목록이 비어 있어요. 위에서 상품을 추가해 주세요.")
else:
    # 중요도 오름차순
    not_purchased.sort(key=lambda x: (x["priority"], x["name"]))

    for item in not_purchased:
        color_class = f"priority-{item['priority']}"
        priority_label = {1: "🔴 1순위", 2: "🟠 2순위", 3: "🟢 3순위"}[item["priority"]]

        with st.container(border=True):
            title_col, action_col = st.columns([4, 1])
            with title_col:
                st.markdown(f"**{item['name']}**　`{item['category']}`")
                st.caption(f"{priority_label}" + (f" · {item['note']}" if item["note"] else ""))
            with action_col:
                if st.button("🛍️ 구매", key=f"buy_{item['id']}", use_container_width=True):
                    st.session_state[f"purchase_open_{item['id']}"] = True

            if st.session_state.get(f"purchase_open_{item['id']}", False):
                with st.form(f"purchase_form_{item['id']}"):
                    pc1, pc2 = st.columns(2)
                    price = pc1.number_input(
                        "개당 가격 (원)",
                        min_value=0,
                        value=int(item["price"]),
                        step=100,
                        key=f"price_{item['id']}"
                    )
                    quantity = pc2.number_input(
                        "수량",
                        min_value=1,
                        value=int(item["quantity"]),
                        step=1,
                        key=f"qty_{item['id']}"
                    )
                    st.caption(f"합계: **{int(price) * int(quantity):,}원**")
                    sc1, sc2 = st.columns(2)
                    confirm = sc1.form_submit_button("구매 완료 ✓", type="primary", use_container_width=True)
                    cancel = sc2.form_submit_button("취소", use_container_width=True)

                    if confirm:
                        item["price"] = int(price)
                        item["quantity"] = int(quantity)
                        item["purchased"] = True
                        item["purchased_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.session_state[f"purchase_open_{item['id']}"] = False
                        st.rerun()
                    if cancel:
                        st.session_state[f"purchase_open_{item['id']}"] = False
                        st.rerun()

            delete_col, _ = st.columns([1, 4])
            with delete_col:
                if st.button("🗑️ 삭제", key=f"delete_{item['id']}"):
                    st.session_state.items = [
                        x for x in st.session_state.items if x["id"] != item["id"]
                    ]
                    st.rerun()

# -------------------------
# 구매 완료 목록
# -------------------------
st.subheader("✅ 카트에 담은 상품")

if not purchased_items:
    st.caption("구매 완료한 상품이 여기에 표시돼요.")
else:
    for item in purchased_items:
        line_total = item["price"] * item["quantity"]
        with st.container(border=True):
            a, b, c = st.columns([3, 2, 1])
            a.markdown(f"**{item['name']}**")
            a.caption(f"{item['category']} · {item['quantity']}개")
            b.markdown(f"**{line_total:,}원**")
            if c.button("↩ 복구", key=f"restore_{item['id']}"):
                item["purchased"] = False
                st.rerun()

# -------------------------
# 메모
# -------------------------
st.subheader("📌 장보기 메모")
st.session_state.memo = st.text_area(
    "메모",
    value=st.session_state.memo,
    placeholder="예: 할인 상품 확인하기, 장바구니 챙기기",
    height=70,
    label_visibility="collapsed"
)

# -------------------------
# 목록 초기화
# -------------------------
with st.expander("⚙️ 관리"):
    if st.button("장보기 목록 전체 초기화", type="secondary"):
        st.session_state.items = []
        st.session_state.memo = ""
        st.rerun()

st.caption("장보기 알림메모 · Streamlit")
