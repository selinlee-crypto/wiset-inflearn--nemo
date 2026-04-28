import pandas as pd
import json
import os
from jinja2 import Environment, FileSystemLoader

def main():
    # 1. 데이터 로드
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'nemo_items.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        return

    df = pd.read_csv(csv_path)

    # 2. 통계 지표 계산
    total_items = len(df)
    avg_deposit = f"{df['deposit'].mean():,.0f}"
    avg_rent = f"{df['monthlyRent'].mean():,.0f}"
    
    no_premium_count = len(df[df['premium'] == 0])
    no_premium_ratio = f"{(no_premium_count / total_items) * 100:.1f}"

    # 3. 차트 데이터 생성
    # Bar Chart: 업종 대분류
    bar_data = df['businessLargeCodeName'].value_counts().head(10)
    
    # Line Chart: 층수별 평균 월세
    line_df = df[(df['floor'] >= -2) & (df['floor'] <= 10)]
    line_data = line_df.groupby('floor')['monthlyRent'].mean().round(0).sort_index()
    
    # Scatter Chart: 면적 대비 보증금 (아웃라이어 제외, 상위 95% 이하만)
    scatter_df = df[(df['size'] < df['size'].quantile(0.95)) & (df['deposit'] < df['deposit'].quantile(0.95))]
    scatter_list = [{"x": round(row['size'], 1), "y": row['deposit']} for _, row in scatter_df.iterrows()]
    
    # Pie Chart: 권리금 유무
    has_premium_count = total_items - no_premium_count

    chart_data = {
        "bar": {
            "labels": bar_data.index.tolist(),
            "values": bar_data.values.tolist()
        },
        "line": {
            "labels": [f"{f}층" if f > 0 else f"B{-f}층" for f in line_data.index.tolist()],
            "values": line_data.values.tolist()
        },
        "scatter": {
            "data": scatter_list
        },
        "pie": {
            "labels": ["유권리 (권리금 있음)", "무권리 (권리금 없음)"],
            "values": [has_premium_count, no_premium_count]
        }
    }

    # 4. 템플릿 렌더링
    template_dir = os.path.join(base_dir, 'src', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('dashboard_template.html')

    output_html = template.render(
        total_items=f"{total_items:,}",
        avg_deposit=avg_deposit,
        avg_rent=avg_rent,
        no_premium_ratio=no_premium_ratio,
        chart_data_json=json.dumps(chart_data, ensure_ascii=False)
    )

    # 5. 파일 저장
    docs_dir = os.path.join(base_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, 'dashboard.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
        
    print(f"Dashboard successfully generated at: {output_path}")

if __name__ == '__main__':
    main()
