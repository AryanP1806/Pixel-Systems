import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product.dart';
import '../models/customer.dart';
import '../models/rental.dart';
import '../models/supplier.dart';

class ApiService {
  static const String baseUrl = 'http://192.168.0.109:8000/api/v1';
  String? _authToken;

  // Login
  Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      );
      if (response.statusCode == 200) {
        _authToken = jsonDecode(response.body)['token'];
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  // Helper for GET requests
  Future<List<dynamic>> _get(String endpoint) async {
    if (_authToken == null) throw Exception('Not logged in');
    final response = await http.get(
      Uri.parse('$baseUrl/$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $_authToken',
      },
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data is Map && data.containsKey('results')) return data['results'];
      if (data is List) return data;
    }
    throw Exception('Failed to load $endpoint');
  }

  // Public Fetch Methods
  Future<List<Product>> getProducts() async =>
      (await _get('products/')).map((j) => Product.fromJson(j)).toList();
  Future<List<Customer>> getCustomers() async =>
      (await _get('customers/')).map((j) => Customer.fromJson(j)).toList();
  Future<List<Rental>> getRentals() async =>
      (await _get('rentals/')).map((j) => Rental.fromJson(j)).toList();
  Future<List<Supplier>> getSuppliers() async =>
      (await _get('suppliers/')).map((j) => Supplier.fromJson(j)).toList();

  // Fetch Pending Approvals
  Future<Map<String, dynamic>> getApprovals() async {
    if (_authToken == null) throw Exception('Not logged in');
    final response = await http.get(
      Uri.parse('$baseUrl/approvals/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $_authToken',
      },
    );
    if (response.statusCode == 200) return jsonDecode(response.body);
    throw Exception('Failed to load approvals');
  }

  // Approve Logic
  Future<bool> approveItem(String type, int id) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/approvals/$type/$id/approve/',
      ), // e.g. approvals/product/1/approve/
      headers: {'Authorization': 'Token $_authToken'},
    );
    return response.statusCode == 200;
  }
}
