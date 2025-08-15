import SwiftUI

struct DurationInputView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    let duration: Duration?
    let isComplete: Bool
    let exerciseId: String
    let exerciseSetId: String
    
    @State private var isEditing = false
    @State private var hoursText = "00"
    @State private var minutesText = "00"
    @State private var secondsText = "00"
    @FocusState private var focusedField: Field?
    
    enum Field: Hashable { case hours, minutes, seconds }
    
    private var displayValue: String {
        guard let seconds = duration?.value else { return "00:00:00" }
        
        let hours = seconds / 3600
        let mins = (seconds % 3600) / 60
        let secs = seconds % 60
        
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, mins, secs)
        } else if mins > 0 {
            return String(format: "%d:%02d", mins, secs)
        } else {
            return "\(secs)s"
        }
    }
    
    var body: some View {
        HStack {
            if isEditing {
                HStack(spacing: 0) {
                    TextField("00", text: $hoursText)
                        .keyboardType(.numberPad)
                        .multilineTextAlignment(.center)
                        .font(Typography.body)
                        .fontWeight(.medium)
                        .focused($focusedField, equals: .hours)
                        .frame(width: 28)
                        .onChange(of: hoursText) { _, newValue in
                            handleTextChange(newValue, field: .hours)
                        }
                        .onSubmit {
                            focusedField = .minutes
                        }

                    Text(":")
                        .font(Typography.body)
                        .fontWeight(.medium)
                        .foregroundColor(Colors.onSurface.opacity(0.6))

                    TextField("00", text: $minutesText)
                        .keyboardType(.numberPad)
                        .multilineTextAlignment(.center)
                        .font(Typography.body)
                        .fontWeight(.medium)
                        .focused($focusedField, equals: .minutes)
                        .frame(width: 28)
                        .onChange(of: minutesText) { _, newValue in
                            handleTextChange(newValue, field: .minutes)
                        }
                        .onSubmit {
                            focusedField = .seconds
                        }
                    
                    Text(":")
                        .font(Typography.body)
                        .fontWeight(.medium)
                        .foregroundColor(Colors.onSurface.opacity(0.6))
                    
                    TextField("00", text: $secondsText)
                        .keyboardType(.numberPad)
                        .multilineTextAlignment(.center)
                        .font(Typography.body)
                        .fontWeight(.medium)
                        .focused($focusedField, equals: .seconds)
                        .frame(width: 28)
                        .onChange(of: secondsText) { _, newValue in
                            handleTextChange(newValue, field: .seconds)
                        }
                        .onSubmit {
                            focusedField = nil
                        }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 2)
                .background(Colors.primary.opacity(0.1))
                .cornerRadius(Radii.small)
                .onAppear {
                    setupInitialValues()
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        focusedField = .hours
                    }
                 }
                 .onChange(of: focusedField) { _, newValue in
                     if newValue == nil {
                         save()
                     }
                 }
            } else {
                Button(action: tryEditor) {
                    Text(displayValue)
                        .font(Typography.body)
                        .fontWeight(.medium)
                        .foregroundColor(duration == nil ? Colors.onSurface.opacity(0.3) :
                                       (isComplete ? Colors.onSurface.opacity(0.5) : Colors.onSurface))
                        .monospacedDigit()
                }
                .buttonStyle(PlainButtonStyle())
            }
            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func setupInitialValues() {
        let totalSeconds = duration?.value ?? 0
        let hours = totalSeconds / 3600
        let mins = (totalSeconds % 3600) / 60
        let secs = totalSeconds % 60
        
        hoursText = hours > 0 ? String(format: "%02d", hours) : ""
        minutesText = mins > 0 ? String(format: "%02d", mins) : ""
        secondsText = secs > 0 ? String(format: "%02d", secs) : ""
    }
    
    private func handleTextChange(_ text: String, field: Field) {
        let filtered = text.filter { $0.isNumber }
        
        if filtered.count >= 2 {
            let truncated = String(filtered.prefix(2))
            
            switch field {
            case .hours:
                hoursText = truncated
                
                if filtered.count > 2 {
                    minutesText = String(filtered.dropFirst(2).prefix(2))
                }
                
                focusedField = .minutes
            case .minutes:
                if let mins = Int(truncated), mins > 59 {
                    minutesText = "59"
                    if filtered.count > 2 {
                        secondsText = String(filtered.dropFirst(2).prefix(2))
                    }
                } else {
                    minutesText = truncated
                    
                    if filtered.count > 2 {
                        secondsText = String(filtered.dropFirst(2).prefix(2))
                    }
                    
                    focusedField = .seconds
                }
            case .seconds:
                if let secs = Int(truncated), secs > 59 {
                    secondsText = "59"
                } else {
                    secondsText = truncated
                }
                
                if filtered.count >= 2 {
                    focusedField = nil
                }
            }
        } else {
            switch field {
            case .hours:
                hoursText = filtered
            case .minutes:
                minutesText = filtered
            case .seconds:
                secondsText = filtered
            }
        }
    }
    
    private func tryEditor() {
        if isComplete || isEditing { return }
        isEditing = true
    }
    
    private func save() {
        isEditing = false
        
        let hours = Int(hoursText) ?? 0
        let minutes = min(59, Int(minutesText) ?? 0)
        let seconds = min(59, Int(secondsText) ?? 0)
        let totalSeconds = max(0, hours * 3600 + minutes * 60 + seconds)
        
        updateMetrics { metrics in
            metrics.duration = Duration(value: totalSeconds)
        }
    }
    
    private func updateMetrics(_ update: (inout ExerciseSessionStateItemMetric) -> Void) {
        guard let state = exerciseSessionManager.currentState,
              let itemIndex = state.items.firstIndex(where: {$0.id == exerciseId}),
              let setIndex = state.items[itemIndex].sets.firstIndex(where: {$0.id == exerciseSetId}) else { return }
        
        var metrics = state.items[itemIndex].sets[setIndex].metrics
        update(&metrics)
        exerciseSessionManager.updateExerciseMetrics(exerciseId: exerciseId, exerciseSetId: exerciseSetId, metrics: metrics)
    }
}

#Preview {
    DurationInputView(
        duration: Duration(value: 3600),
        isComplete: false,
        exerciseId: "id",
        exerciseSetId: "setid"
    )
}
