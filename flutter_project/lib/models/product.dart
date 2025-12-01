class Product {
  final int id;
  final String assetId;
  final String brand;
  final String modelNo;
  final String condition;

  Product({
    required this.id,
    required this.assetId,
    required this.brand,
    required this.modelNo,
    required this.condition,
  });

  // This factory method converts the JSON from Django into a clean Product object
  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] ?? 0,
      assetId: json['asset_id'] ?? 'Unknown ID',
      brand: json['brand'] ?? 'Unknown Brand',
      modelNo: json['model_no'] ?? 'Unknown Model',
      condition: json['condition_status'] ?? 'Unknown',
    );
  }
}
