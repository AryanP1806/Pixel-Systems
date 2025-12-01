import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ApprovalDashboardScreen extends StatefulWidget {
  final ApiService apiService;
  const ApprovalDashboardScreen({super.key, required this.apiService});

  @override
  State<ApprovalDashboardScreen> createState() =>
      _ApprovalDashboardScreenState();
}

class _ApprovalDashboardScreenState extends State<ApprovalDashboardScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _fetchData();
  }

  void _fetchData() async {
    try {
      final data = await widget.apiService.getApprovals();
      setState(() {
        _data = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  void _approve(String type, int id) async {
    final success = await widget.apiService.approveItem(type, id);
    if (success) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Approved Successfully!")));
      _fetchData(); // Refresh list
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Pending Approvals"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Assets"),
            Tab(text: "Rentals"),
            Tab(text: "Customers"),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildList(
                  _data?['products'] ?? [],
                  'product',
                  'brand',
                  'model_no',
                ),
                _buildList(
                  _data?['rentals'] ?? [],
                  'rental',
                  'customer_name',
                  'asset_name',
                ),
                _buildList(
                  _data?['customers'] ?? [],
                  'customer',
                  'name',
                  'phone_number_primary',
                ),
              ],
            ),
    );
  }

  Widget _buildList(List items, String type, String titleKey, String subKey) {
    if (items.isEmpty) return const Center(child: Text("No pending items"));
    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (ctx, i) {
        final item = items[i];
        return Card(
          margin: const EdgeInsets.all(8),
          child: ListTile(
            title: Text(item[titleKey] ?? 'Unknown'),
            subtitle: Text(item[subKey] ?? ''),
            trailing: ElevatedButton(
              onPressed: () => _approve(type, item['id']),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
              child: const Text("Approve"),
            ),
          ),
        );
      },
    );
  }
}
