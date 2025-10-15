from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Загружаем Excel-каталог
df = pd.read_excel("catalog.xlsx")
df = df.fillna("")

@app.route("/", methods=["GET"])
def index():
    brand_filter = request.args.get("brand", "")
    name_filter = request.args.get("name", "")
    size_filter = request.args.get("size", "")
    gender_filter = request.args.get("gender", "")

    filtered_df = df.copy()

    # Фильтрация
    if brand_filter:
        filtered_df = filtered_df[filtered_df["Brand"].str.contains(brand_filter, case=False, na=False)]
    if name_filter:
        filtered_df = filtered_df[filtered_df["Name"].str.contains(name_filter, case=False, na=False)]
    if size_filter:
        filtered_df = filtered_df[filtered_df["Name"].str.contains(size_filter, case=False, na=False)]
    if gender_filter:
        filtered_df = filtered_df[filtered_df["Name"].str.contains(gender_filter, case=False, na=False)]

    products = filtered_df.to_dict(orient="records")
    return render_template("index.html", products=products)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
