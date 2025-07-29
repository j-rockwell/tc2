import Foundation
import os

class AppLogger {
    private let logger: Logger
    private let category: String
    
    init(subsystem: String, category: String) {
        self.logger = Logger(subsystem: subsystem, category: category)
        self.category = category
    }
    
    func info(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        prime(message, level: "INFO")
    }
    
    func warning(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        prime(message, level: "WARNING")
    }
    
    func error(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        prime(message, level: "ERROR")
    }
    
    func fault(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        prime(message, level: "FAULT")
    }
    
    private func prime(_ message: String, level: String) {
        let msg = format(message, level: level, file: #file, function: #function, line: #line)
        logger.debug("\(msg)")
        #if DEBUG
        print("[\(category.uppercased())] \(msg)")
        #endif
    }
    
    private func format(_ message: String, level: String, file: String, function: String, line: Int) -> String {
        let fileName = URL(fileURLWithPath: file).lastPathComponent
        let timestamp = DateFormatter.formatTime.string(from: Date())
        return "\(timestamp) [\(level)] \(fileName):\(function):\(line): \(message)"
    }
}

extension DateFormatter {
    static let formatTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss:.SSS"
        return formatter
    }()
}
