from rest_framework import serializers
from .models import Product, Stock, StockProduct


class ProductSerializer(serializers.ModelSerializer):
    # настройте сериализатор для продукта
    class Meta:
        model = Product
        fields = '__all__'


class ProductPositionSerializer(serializers.ModelSerializer):
    # настройте сериализатор для позиции продукта на складе
    class Meta:
        model = StockProduct
        exclude = ('id', 'stock')


class StockSerializer(serializers.ModelSerializer):
    positions = ProductPositionSerializer(many=True)

    class Meta:
        model = Stock
        fields = '__all__'
    # настройте сериализатор для склада


    def create(self, validated_data):
        # достаем связанные данные для других таблиц
        positions = validated_data.pop('positions')

        # создаем склад по его параметрам
        stock = super().create(validated_data)

        for position_data in positions:
            product = position_data.pop('product')
            StockProduct.objects.create(product=product, stock=stock, **position_data)
        return stock
        # здесь вам надо заполнить связанные таблицы
        # в нашем случае: таблицу StockProduct
        # с помощью списка positions



    def update(self, instance, validated_data):
        # достаем связанные данные для других таблиц
        positions = validated_data.pop('positions')

        # обновляем склад по его параметрам
        stock = super().update(instance, validated_data)

        # здесь вам надо обновить связанные таблицы
        # в нашем случае: таблицу StockProduct
        # с помощью списка positions
        position_ids = [position['id'] for position in positions if 'id' in position]
        position_objs = positions.objects.filter(stock=stock, id__in=position_ids)
        existing_positions = {position.id: position for position in position_objs}
        new_positions = []
        for position_data in positions:
            if 'id' in position_data:
                position = existing_positions.pop(position_data['id'])
                product_data = position_data.pop('product')
                product = position.product
                Product.objects.update_or_create(id=product.id, defaults=product_data)
                for attr, value in position_data.items():
                    setattr(position, attr, value)
                position.save()
            else:
                product = position_data.pop('product')
                new_positions.append(StockProduct(product=product, stock=stock, **position_data))
        StockProduct.objects.bulk_create(new_positions)
        for position in existing_positions.values():
            position.delete()
        return stock
