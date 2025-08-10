package com.editor;

public class Plugin {
    public static void main(String[] args) {
        System.out.println("Java Plugin: Initializing...");

        // 1. Create a new buffer using the native bridge
        long bufferPtr = NativeBridge.createBuffer();
        System.out.println("Java Plugin: Buffer created at address: " + bufferPtr);

        // 2. Load a file (e.g., shortcuts.txt)
        String filename = "shortcuts.txt";
        NativeBridge.loadFile(bufferPtr, filename);
        System.out.println("Java Plugin: Loaded file '" + filename + "'");

        // 3. Get the line count and print it
        int lineCount = NativeBridge.getLineCount(bufferPtr);
        System.out.println("Java Plugin: The file has " + lineCount + " lines.");

        // 5. Find a character in the first line using the assembly function
        if (lineCount > 0) {
            byte byteToFind = 'a'; // Find the letter 'a'
            long foundIndex = NativeBridge.findByteInLine(bufferPtr, 0, byteToFind);
            System.out.println("Java Plugin: Searching for '" + (char)byteToFind + "' in the first line...");
            if (foundIndex != -1) {
                System.out.println("Java Plugin: Found at byte index: " + foundIndex);
            } else {
                System.out.println("Java Plugin: Not found.");
            }
        }

        // 6. Clean up the buffer
        NativeBridge.destroyBuffer(bufferPtr);
        System.out.println("Java Plugin: Buffer destroyed.");

        System.out.println("Java Plugin: Execution finished.");
    }
}
