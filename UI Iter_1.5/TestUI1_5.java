// cd ~/Desktop
// javac -cp ".:jxmapviewer2-2.8.jar:commons-logging-1.2.jar" TestUI1_5.java
// java -cp ".:jxmapviewer2-2.8.jar:commons-logging-1.2.jar" TestUI1_5

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

// External Map Libraries
import org.jxmapviewer.JXMapViewer;
import org.jxmapviewer.OSMTileFactoryInfo;
import org.jxmapviewer.viewer.DefaultTileFactory;
import org.jxmapviewer.viewer.GeoPosition;
import org.jxmapviewer.viewer.TileFactoryInfo;
import org.jxmapviewer.input.PanMouseInputListener;
import org.jxmapviewer.input.ZoomMouseWheelListenerCursor;

public class TestUI1_5 extends JFrame {

    // UI Components
    private JPanel leftPanel;
    private JXMapViewer mapViewer;
    private JButton btnServer, btnClient, btnKeyControl, btnTakeoff, btnFindCoords;
    private JButton btnOpenMirror, btnPlaceholder, btnCenterMap, btnGridzone, btnExitGridzone;

    // State Variables
    private boolean isMirrorOpen = false;
    private boolean isServerRunning = false;
    
    // Default Map Location (Isla Vista, CA)
    private final GeoPosition HOME_LOCATION = new GeoPosition(34.4133, -119.8610);

    public TestUI1_5() {
        setTitle("Drone Control UI - Iteration 1.5 (Live Map)");
        setSize(1280, 800);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout());

        initComponents();
        buildLayout();
        attachListeners();
    }

    private void initComponents() {
        // --- THE FIX 1: Standard Browser User-Agent ---
        System.setProperty("http.agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36");
        
        // --- Initialize Live Map ---
        mapViewer = new JXMapViewer();
        
        // --- THE FIX 2: Force HTTPS for OpenStreetMap ---
        TileFactoryInfo info = new OSMTileFactoryInfo() {
            @Override
            public String getTileUrl(int x, int y, int zoom) {
                int z = getTotalMapZoom() - zoom;
                return "https://tile.openstreetmap.org/" + z + "/" + x + "/" + y + ".png";
            }
        };
        
        DefaultTileFactory tileFactory = new DefaultTileFactory(info);
        mapViewer.setTileFactory(tileFactory);
        
        // Set focus to Isla Vista and zoom level
        mapViewer.setZoom(5); 
        mapViewer.setAddressLocation(HOME_LOCATION);

        // Add mouse interactions (pan and zoom)
        PanMouseInputListener mia = new PanMouseInputListener(mapViewer);
        mapViewer.addMouseListener(mia);
        mapViewer.addMouseMotionListener(mia);
        mapViewer.addMouseWheelListener(new ZoomMouseWheelListenerCursor(mapViewer));

        // Create an overlay button for exiting Gridzone
        mapViewer.setLayout(null); // Absolute layout for overlay
        btnExitGridzone = new JButton("Exit Gridzone");
        btnExitGridzone.setBounds(20, 20, 150, 40);
        btnExitGridzone.setVisible(false);
        mapViewer.add(btnExitGridzone);

        // --- Initialize Control Buttons (This is what went missing!) ---
        btnServer = createMenuButton("Run Server (i)");
        btnServer.setEnabled(false);

        btnClient = createMenuButton("Run Client (ii)");
        btnClient.setEnabled(false);

        btnKeyControl = createMenuButton("Run Key Control (iii)");
        btnTakeoff = createMenuButton("Run Takeoff-Forward Test (iv)");
        btnFindCoords = createMenuButton("Run Find Coords (v)");

        btnOpenMirror = new JButton("Open Mirror (1)");
        btnPlaceholder = new JButton("Placeholder (2)");
        btnCenterMap = createMenuButton("Center Map");
        btnGridzone = createMenuButton("Define Gridzone");
    }

    private void buildLayout() {
        leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        leftPanel.setPreferredSize(new Dimension(280, 800));

        // Group 1: Python Scripts
        leftPanel.add(btnServer);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 5)));
        leftPanel.add(btnClient);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 5)));
        leftPanel.add(btnKeyControl);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 5)));
        leftPanel.add(btnTakeoff);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 5)));
        leftPanel.add(btnFindCoords);
        
        leftPanel.add(Box.createRigidArea(new Dimension(0, 30)));

        // Group 2: Apps
        JPanel miniGrid = new JPanel(new GridLayout(1, 2, 10, 0));
        miniGrid.setMaximumSize(new Dimension(240, 50));
        miniGrid.add(btnOpenMirror);
        miniGrid.add(btnPlaceholder);
        leftPanel.add(miniGrid);

        leftPanel.add(Box.createRigidArea(new Dimension(0, 30)));

        // Group 3: Map Controls
        leftPanel.add(btnCenterMap);
        leftPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        leftPanel.add(btnGridzone);

        add(leftPanel, BorderLayout.WEST);
        add(mapViewer, BorderLayout.CENTER);
    }

    private void attachListeners() {
        // Application Macros
        btnOpenMirror.addActionListener(e -> {
            // Using iPhone Mirroring natively on macOS
            executeTerminalCommand(new String[]{"open", "-a", "iPhone Mirroring"});
            isMirrorOpen = true;
            btnServer.setEnabled(true);
            btnOpenMirror.setBackground(Color.GREEN);
        });

        // Python Script Macros
        btnServer.addActionListener(e -> {
            executeTerminalCommand(new String[]{"python3", "/Users/dyv/Desktop/droneproject/Neo 2/drone_detect-automate_Server.py"});
            isServerRunning = true;
            btnClient.setEnabled(true);
            btnServer.setBackground(Color.GREEN);
        });

        btnClient.addActionListener(e -> {
            executeTerminalCommand(new String[]{"python3", "/Users/dyv/Desktop/droneproject/Neo 2/drone_detect_MIRROR_CLIENT.py"});
        });

        btnKeyControl.addActionListener(e -> {
            executeTerminalCommand(new String[]{"python3", "/Users/dyv/Desktop/droneproject/Neo 2/Neo-ANTQD/key-flight-ANTIQUATED.py"});
        });

        btnTakeoff.addActionListener(e -> {
            executeTerminalCommand(new String[]{"python3", "/Users/dyv/Desktop/droneproject/Neo 2/TakeOff&Forward2.py"});
        });

        btnFindCoords.addActionListener(e -> {
            executeTerminalCommand(new String[]{"python3", "/Users/dyv/Desktop/droneproject/testScripts/find_coords_iOS.py_"});
        });

        // Map Macros
        btnCenterMap.addActionListener(e -> {
            mapViewer.setAddressLocation(HOME_LOCATION);
            mapViewer.setZoom(5);
        });

        btnGridzone.addActionListener(e -> {
            remove(leftPanel);
            btnExitGridzone.setVisible(true);
            btnExitGridzone.setLocation(mapViewer.getWidth() - 170, 20); // Top Right
            revalidate();
            repaint();
        });

        btnExitGridzone.addActionListener(e -> {
            add(leftPanel, BorderLayout.WEST);
            btnExitGridzone.setVisible(false);
            revalidate();
            repaint();
        });
    }

    private void executeTerminalCommand(String[] command) {
        new Thread(() -> {
            try {
                ProcessBuilder pb = new ProcessBuilder(command);
                pb.redirectErrorStream(true);
                Process process = pb.start();
                
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    System.out.println("--- Executing: " + String.join(" ", command) + " ---");
                    while ((line = reader.readLine()) != null) {
                        System.out.println(line);
                    }
                }
            } catch (IOException ex) {
                System.err.println("Failed to execute command: " + ex.getMessage());
            }
        }).start();
    }

    private JButton createMenuButton(String text) {
        JButton btn = new JButton(text);
        btn.setMaximumSize(new Dimension(240, 40));
        btn.setAlignmentX(Component.CENTER_ALIGNMENT);
        return btn;
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new TestUI1_5().setVisible(true);
        });
    }
}