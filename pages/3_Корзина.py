<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Корзина</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .cart-container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .cart-item {
            display: flex;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #eee;
        }
        .item-image {
            width: 120px;
            height: 120px;
            background-color: #f0f0f0;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 20px;
            color: #999;
        }
        .item-details {
            flex-grow: 1;
        }
        .item-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .item-color, .item-size {
            color: #666;
            margin-bottom: 3px;
        }
        .item-price {
            font-weight: bold;
            margin-top: 10px;
            font-size: 16px;
        }
        .remove-link {
            color: #ff3b30;
            text-decoration: none;
            margin-top: 10px;
            display: inline-block;
        }
        .quantity-controls {
            display: flex;
            align-items: center;
            margin-top: 15px;
        }
        .quantity-btn {
            width: 30px;
            height: 30px;
            background-color: #f0f0f0;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        .quantity-input {
            width: 40px;
            height: 30px;
            text-align: center;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 0 10px;
        }
    </style>
</head>
<body>
    <div class="cart-container">
        <h1>Корзина</h1>
        
        <div class="cart-item">
            <div class="item-image">
                [Фото товара]
            </div>
            <div class="item-details">
                <div class="item-name">Mizuno Racer S</div>
                <div class="item-color">Цвет: grey</div>
                <div class="item-size">Размер: 1</div>
                <div class="item-price">Цена: 60 000 т</div>
                <a href="#" class="remove-link">Удалить</a>
                
                <div class="quantity-controls">
                    <button class="quantity-btn">-</button>
                    <input type="text" class="quantity-input" value="1">
                    <button class="quantity-btn">+</button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>