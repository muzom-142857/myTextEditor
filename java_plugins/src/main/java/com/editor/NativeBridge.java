package com.editor;

public class NativeBridge {
    // Load the JNI bridge library
    static {
        System.loadLibrary("jni_bridge");
    }

    // Native methods corresponding to the Rust core engine functions
    public static native long createBuffer();
    public static native void destroyBuffer(long bufferPtr);
    public static native void loadFile(long bufferPtr, String filename);
    public static native void saveFile(long bufferPtr, String filename);
    public static native int getLineCount(long bufferPtr);
    public static native long findByteInLine(long bufferPtr, int line, byte b);
    // ... other native methods will be added here
}
