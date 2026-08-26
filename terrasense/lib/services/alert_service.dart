import 'dart:async';
import 'dart:convert';
import 'package:geolocator/geolocator.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'alert_sound_service.dart';

class AlertService {
  static WebSocketChannel? _channel;
  static Timer? _reconnectTimer;

  // ⚠️ Replace with your FastAPI server's local IP or domain
  static const String wsUrl = 'ws://192.168.137.1:8000/ws/device';

  static void start() {
    _connect();
  }

  static void _connect() {
    try {
      print('[AlertService] Connecting to WebSocket...');
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _channel!.stream.listen(
        (message) => _onMessage(message),
        onDone: () {
          print('[AlertService] WebSocket closed. Reconnecting...');
          _scheduleReconnect();
        },
        onError: (error) {
          print('[AlertService] WebSocket error: $error');
          _scheduleReconnect();
        },
      );

      print('[AlertService] Connected.');
    } catch (e) {
      print('[AlertService] Connection failed: $e');
      _scheduleReconnect();
    }
  }

  static void _onMessage(dynamic raw) async {
    try {
      print('[AlertService] Message received: $raw');
      final data = jsonDecode(raw);

      final double emergencyLat = double.parse(data['lat'].toString());
      final double emergencyLng = double.parse(data['lng'].toString());
      final String message = data['message'] ?? 'Emergency Alert!';

      // 📍 Fetch real-time device location when alert is received
      final Position? devicePosition = await _getLocation();

      if (devicePosition == null) {
        print('[AlertService] Could not fetch location. Triggering alert as fallback.');
        await AlertSoundService.playAlert(message, 0.0);
        return;
      }

      // Calculate distance between current location and emergency target in meters
      final double distanceMeters = Geolocator.distanceBetween(
        devicePosition.latitude,
        devicePosition.longitude,
        emergencyLat,
        emergencyLng,
      );

      final double distanceKm = distanceMeters / 1000;
      print('[AlertService] Device distance to incident: ${distanceKm.toStringAsFixed(2)} km');

      // 🚨 Trigger alert if device is within 15 km radius
      if (distanceKm <= 15.0) {
        print('[AlertService] 🚨 Device within 15km! Playing alert.');
        await AlertSoundService.playAlert(message, distanceKm);
      } else {
        print('[AlertService] ✅ Outside 15km threshold. Alert ignored.');
      }
    } catch (e) {
      print('[AlertService] Error processing alert message: $e');
    }
  }

  static Future<Position?> _getLocation() async {
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 8),
        ),
      );
    } catch (e) {
      print('[AlertService] High-accuracy GPS request failed. Using last known location.');
      try {
        return await Geolocator.getLastKnownPosition();
      } catch (_) {
        return null;
      }
    }
  }

  static void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () {
      _connect();
    });
  }

  static void stop() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
  }
}