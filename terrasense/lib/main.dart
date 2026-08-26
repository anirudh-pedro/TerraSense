import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'services/foreground_service_manager.dart';
import 'services/alert_sound_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Init foreground service config
  ForegroundServiceManager.init();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Emergency Alert',
      navigatorKey: AlertSoundService.navigatorKey,
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    await _requestPermissions();
    await ForegroundServiceManager.startService();
  }

  Future<void> _requestPermissions() async {
    // Location permission
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    // Ask for always-on location (background)
    if (permission == LocationPermission.whileInUse) {
      await Geolocator.requestPermission();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.shield, color: Colors.red, size: 80),
            const SizedBox(height: 20),
            const Text(
              '🚨 Emergency Alert System',
              style: TextStyle(color: Colors.white, fontSize: 22),
            ),
            const SizedBox(height: 10),
            const Text(
              'Service is running in background',
              style: TextStyle(color: Colors.green, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
