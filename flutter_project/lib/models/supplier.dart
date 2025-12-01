class Supplier {
  final int id;
  final String name;
  final String phone;
  final String email;

  Supplier({
    required this.id,
    required this.name,
    required this.phone,
    required this.email,
  });

  factory Supplier.fromJson(Map<String, dynamic> json) {
    return Supplier(
      id: json['id'] ?? 0,
      name: json['name'] ?? 'Unknown',
      phone: json['phone_primary'] ?? '',
      email: json['email'] ?? '',
    );
  }
}
