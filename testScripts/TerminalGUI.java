import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import javax.swing.*;

public class TerminalGUI {

    public static void main(String[] args) {
        SwingUtilities.invokeLater(TerminalGUI::createAndShowGUI);
    }

    private static void createAndShowGUI() {
        // Main Window Setup
        JFrame frame = new JFrame("Mac Terminal UI Test");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(750, 400); // Slightly wider to accommodate the longer button text
        frame.setLayout(new BorderLayout());

        // Terminal Output Display
        JTextArea outputArea = new JTextArea();
        outputArea.setEditable(false);
        outputArea.setBackground(Color.BLACK);
        outputArea.setForeground(Color.GREEN);
        outputArea.setFont(new Font("Monospaced", Font.PLAIN, 13));
        
        JScrollPane scrollPane = new JScrollPane(outputArea);
        frame.add(scrollPane, BorderLayout.CENTER);

        // Buttons Setup
        JPanel buttonPanel = new JPanel();
        buttonPanel.setLayout(new FlowLayout());

        JButton btn1 = new JButton("Run Joystick Script");
        JButton btn2 = new JButton("System Date (date)");
        JButton btn3 = new JButton("Test Echo");

        // The path is wrapped in single quotes to handle the spaces in the directory names
        String scriptCommand = "python3 '/Users/dyv/Desktop/droneproject/Antiquated Scripts/Cue System Scripts/joystick server:clients/joystick.py'";

        // Assign terminal commands to buttons
        btn1.addActionListener(e -> executeCommand(scriptCommand, outputArea));
        btn2.addActionListener(e -> executeCommand("date", outputArea));
        btn3.addActionListener(e -> executeCommand("echo 'UI to Mac Terminal connection successful!'", outputArea));

        buttonPanel.add(btn1);
        buttonPanel.add(btn2);
        buttonPanel.add(btn3);

        frame.add(buttonPanel, BorderLayout.SOUTH);
        
        // Center the window on the screen and display it
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    private static void executeCommand(String command, JTextArea outputArea) {
        outputArea.append("user@macbook % " + command + "\n");
        
        try {
            // Execute using bash to respect the quoted path and environment
            ProcessBuilder processBuilder = new ProcessBuilder("bash", "-c", command);
            processBuilder.redirectErrorStream(true); 
            
            Process process = processBuilder.start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            
            String line;
            while ((line = reader.readLine()) != null) {
                outputArea.append(line + "\n");
            }
            
            process.waitFor();
            outputArea.append("\n"); 
            
        } catch (Exception ex) {
            outputArea.append("Error executing command: " + ex.getMessage() + "\n\n");
        }
        
        outputArea.setCaretPosition(outputArea.getDocument().getLength()); 
    }
}