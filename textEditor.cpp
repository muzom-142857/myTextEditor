#include <cstddef>

// Rust 라이브러리 함수 선언
extern "C" {
    void* create_buffer();
    void destroy_buffer(void* buffer);
    void load_file(void* buffer, const char* filename);
    void save_file(void* buffer, const char* filename);
    size_t get_line_count(void* buffer);
    void get_line(void* buffer, size_t lineNumber, const char** linePtr, size_t* lineLength);
    void insert_text(void* buffer, size_t y, size_t unicode_x, const char* text);
    void delete_text(void* buffer, size_t y, size_t unicode_x, size_t unicode_length);
    void split_line(void* buffer, size_t y, size_t unicode_x);
    void join_lines(void* buffer, size_t y);
    size_t get_unicode_length_for_line(void* buffer, size_t y);
    void copy_text(void* buffer, size_t y, size_t unicode_x, size_t unicode_length);
    void paste_text(void* buffer, size_t y, size_t unicode_x);
    void replace_all(void* buffer, const char* old_str, const char* new_str);
    void find_next(void* buffer, const char* search_str, size_t y, size_t unicode_x, size_t* found_y, size_t* found_x);
    void undo(void* buffer);
    void redo(void* buffer);
    void free_string(char* s);
}

// C++ 래퍼 함수들
extern "C" {
    void* createBuffer() { return create_buffer(); }
    void destroyBuffer(void* buffer) { destroy_buffer(buffer); }
    void loadFile(void* buffer, const char* filename) { load_file(buffer, filename); }
    void saveFile(void* buffer, const char* filename) { save_file(buffer, filename); }
    size_t getLineCount(void* buffer) { return get_line_count(buffer); }
    void getLine(void* buffer, size_t lineNumber, const char** linePtr, size_t* lineLength) { get_line(buffer, lineNumber, linePtr, lineLength); }
    void insertText(void* buffer, size_t y, size_t unicode_x, const char* text, size_t length) { insert_text(buffer, y, unicode_x, text); }
    void deleteText(void* buffer, size_t y, size_t unicode_x, size_t unicode_length) { delete_text(buffer, y, unicode_x, unicode_length); }
    void splitLine(void* buffer, size_t y, size_t unicode_x) { split_line(buffer, y, unicode_x); }
    void joinLines(void* buffer, size_t y) { join_lines(buffer, y); }
    size_t getUnicodeLength(void* buffer, size_t y) { return get_unicode_length_for_line(buffer, y); }
    void copyText(void* buffer, size_t y, size_t unicode_x, size_t unicode_length) { copy_text(buffer, y, unicode_x, unicode_length); }
    void pasteText(void* buffer, size_t y, size_t unicode_x) { paste_text(buffer, y, unicode_x); }
    void replaceAll(void* buffer, const char* old_str, const char* new_str) { replace_all(buffer, old_str, new_str); }
    void findNext(void* buffer, const char* search_str, size_t y, size_t unicode_x, size_t* found_y, size_t* found_x) { find_next(buffer, search_str, y, unicode_x, found_y, found_x); }
    void undoBuffer(void* buffer) { undo(buffer); }
    void redoBuffer(void* buffer) { redo(buffer); }
    void freeString(char* s) { free_string(s); }
}