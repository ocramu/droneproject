import java.awt.*;
import java.awt.event.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import javax.swing.*;

public class TestUI1 extends JFrame {

    // UI Components
    private JPanel leftPanel;
    private MapPanel mapPanel;
    private JButton btnServer, btnClient, btnKeyControl, btnTakeoff, btnFindCoords;
    private JButton btnOpenMirror, btnPlaceholder, btnCenterMap, btnGridzone;

    // State Variables
    private boolean isMirrorOpen = false;
    private boolean isServerRunning = false;

    public TestUI1() {
        setTitle("Drone Control UI - Iteration 1");
        // MacBook Air standard-ish desktop window size
        setSize(1280, 800);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout());

        initComponents();
        buildLayout();
        attachListeners();
    }

    private void initComponents() {
        // Initialize Map
        mapPanel = new MapPanel();

        // Initialize Buttons
        btnServer = createMenuButton("Run Server (i)");
        btnServer.setEnabled(false); // Waits for Mirror

        btnClient = createMenuButton("Run Client (ii)");
        btnClient.setEnabled(false); // Waits for Server

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
        add(mapPanel, BorderLayout.CENTER);
    }

    private void attachListeners() {
        // Application Macros
        btnOpenMirror.addActionListener(e -> {
            executeTerminalCommand(new String[]{"open", "-a", "iPhone Mirroring"});
            isMirrorOpen = true;
            btnServer.setEnabled(true);
            btnOpenMirror.setBackground(Color.GREEN); // Visual feedback
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
            mapPanel.centerMap();
        });

        btnGridzone.addActionListener(e -> {
            // Remove the left panel to allow the map to fill the screen
            remove(leftPanel);
            mapPanel.setGridzoneMode(true);
            revalidate();
            repaint();
        });

        // Callback from MapPanel to exit Gridzone
        mapPanel.setExitGridzoneAction(e -> {
            add(leftPanel, BorderLayout.WEST);
            mapPanel.setGridzoneMode(false);
            revalidate();
            repaint();
        });
    }

    /**
     * Executes external terminal commands via ProcessBuilder.
     * This abstracts the OS-level calls so you only need to change the string array later for Windows.
     */
    private void executeTerminalCommand(String[] command) {
        new Thread(() -> {
            try {
                ProcessBuilder pb = new ProcessBuilder(command);
                pb.redirectErrorStream(true);
                Process process = pb.start();
                
                // Read terminal output asynchronously to prevent UI freezing
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

    // --- Custom Draggable Map Panel ---
    class MapPanel extends JPanel {
        private int offsetX = 0, offsetY = 0;
        private int dragStartX, dragStartY;
        private boolean isGridzone = false;
        private JButton btnExitGridzone;

        public MapPanel() {
            setBackground(new Color(212, 228, 247)); // Mockup blue
            setLayout(null); // Absolute positioning for the exit button overlay

            btnExitGridzone = new JButton("Exit Gridzone");
            btnExitGridzone.setBounds(20, 20, 150, 40);
            btnExitGridzone.setVisible(false);
            add(btnExitGridzone);

            // Dragging logic
            addMouseListener(new MouseAdapter() {
                public void mousePressed(MouseEvent e) {
                    dragStartX = e.getX() - offsetX;
                    dragStartY = e.getY() - offsetY;
                }
            });

            addMouseMotionListener(new MouseMotionAdapter() {
                public void mouseDragged(MouseEvent e) {
                    offsetX = e.getX() - dragStartX;
                    offsetY = e.getY() - dragStartY;
                    repaint();
                }
            });
        }

        public void centerMap() {
            offsetX = 0;
            offsetY = 0;
            repaint();
        }

        public void setGridzoneMode(boolean enabled) {
            this.isGridzone = enabled;
            btnExitGridzone.setVisible(enabled);
            // Move button to top right when in full screen
            if (enabled) {
                btnExitGridzone.setLocation(getWidth() - 170, 20);
            }
        }

        public void setExitGridzoneAction(ActionListener listener) {
            btnExitGridzone.addActionListener(listener);
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            
            // Draw a simulated 1x4 mile grid based on offset
            g2d.setColor(new Color(180, 200, 220));
            int gridSize = 100;
            for (int i = -2000; i < 2000; i += gridSize) {
                g2d.drawLine(i + offsetX, -2000 + offsetY, i + offsetX, 2000 + offsetY);
                g2d.drawLine(-2000 + offsetX, i + offsetY, 2000 + offsetX, i + offsetY);
            }

            // Draw center point marker
            int centerX = getWidth() / 2 + offsetX;
            int centerY = getHeight() / 2 + offsetY;
            
            g2d.setColor(Color.RED);
            g2d.fillOval(centerX - 5, centerY - 5, 10, 10);
            
            g2d.setColor(Color.BLACK);
            g2d.setFont(new Font("Arial", Font.BOLD, 14));
            g2d.drawString("Computer Location: Isla Vista, CA", centerX + 10, centerY + 5);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new TestUI1().setVisible(true);
        });
    }
}