import os
import math
from flask import Flask, abort, request, jsonify
import pymysql
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

swaggerui_blueprint = get_swaggerui_blueprint(
    base_url='/docs',
    api_url='/static/openapi.yaml',
)
app.register_blueprint(swaggerui_blueprint)

MAX_PAGE_SIZE = 50

def remove_null_fields(obj):
    return {k: v for k, v in obj.items() if v is not None}

@app.route("/reviews")
def reviews():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', MAX_PAGE_SIZE))
    page_size = min(page_size, MAX_PAGE_SIZE)
    include_sentiment = int(request.args.get('include_sentiment', 0))

    db_conn = pymysql.connect(host="localhost", user="root", password=os.getenv('sql_key'), database="TA",
                              cursorclass=pymysql.cursors.DictCursor)

    with db_conn.cursor() as cursor:
        if include_sentiment:
            cursor.execute("""
                SELECT 
                    name AS Name,
                    city AS City,
                    first_cuisine AS Cuisine,
                    price_range AS Price_Range,
                    rating AS Rating,
                    sentiment AS Sentiment FROM reviews
                ORDER BY name
                LIMIT %s
                OFFSET %s
            """, (page_size, (page-1) * page_size))
        else:
            cursor.execute("""
                SELECT 
                    name AS Name,
                    city AS City,
                    first_cuisine AS Cuisine,
                    price_range AS Price_Range,
                    rating AS Rating FROM reviews
                ORDER BY name
                LIMIT %s
                OFFSET %s
            """, (page_size, (page-1) * page_size))
        reviews = cursor.fetchall()

    with db_conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM reviews")
        total = cursor.fetchone()
        last_page = math.ceil(total['total'] / page_size)

    db_conn.close()
    return {
        'reviews': reviews,
        'next_page': f'/reviews?page={page+1}&page_size={page_size}&include_sentiment={include_sentiment}' if page < last_page else None,
        'last_page': f'/reviews?page={last_page}&page_size={page_size}&include_sentiment={include_sentiment}',
    }

@app.route("/reviews/<name>")
def review(name):
    db_conn = pymysql.connect(host="localhost", user="root", password=os.getenv('sql_key'), database="TA",
                              cursorclass=pymysql.cursors.DictCursor)

    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                name AS Name,
                city AS City,
                first_cuisine AS Cuisine,
                price_range AS Price_Range,
                rating AS Rating,
                sentiment AS Sentiment,
                cleaned_reviews AS Reviews
            FROM reviews 
            WHERE name=%s
        """, (name,))
        review = cursor.fetchone()

    if not review:
        db_conn.close()
        abort(404)

    review = remove_null_fields(review)
    db_conn.close()
    return review

@app.route("/reviews/create", methods=["POST"])
def create_review():
    data = request.json
    
    db_conn = pymysql.connect(host="localhost", user="root", password=os.getenv('sql_key'), database="TA",
                              cursorclass=pymysql.cursors.DictCursor)
    
    with db_conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO reviews (name, city, first_cuisine, price_range, rating, sentiment, cleaned_reviews)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data['name'], data['city'], data['cuisine'], data['price_range'], data['rating'], data['sentiment'], data['reviews']))
        db_conn.commit()
    
    db_conn.close()
    
    return jsonify({'message': 'Review created successfully'})

if __name__ == "__main__":
    app.run(debug=True)



# curl -X POST \
#   http://localhost:8080/reviews/create \
#   -H "Content-Type: application/json" \
#   -d '{
#         "name": "Restaurant ABC",
#         "city": "New York",
#         "cuisine": "Italian",
#         "price_range": "$$",
#         "rating": 4.5,
#         "sentiment": "positive",
#         "reviews": "Excellent food and service!"
#       }'






    