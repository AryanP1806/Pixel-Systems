class Rental {
  final int id;
  final String customerName;
  final String assetId;
  final String status;
  final String startDate;

  Rental({
    required this.id,
    required this.customerName,
    required this.assetId,
    required this.status,
    required this.startDate,
  });

  factory Rental.fromJson(Map<String, dynamic> json) {
    return Rental(
      id: json['id'] ?? 0,
      customerName: json['customer_name'] ?? 'Unknown',
      assetId: json['asset_id_display'] ?? 'Unknown',
      status: json['status'] ?? 'ongoing',
      startDate: json['rental_start_date'] ?? '',
    );
  }
}
