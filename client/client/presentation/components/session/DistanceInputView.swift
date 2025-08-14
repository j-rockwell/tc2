import SwiftUI

struct DistanceInputView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    let distance: Distance?
    let isComplete: Bool
    let exerciseId: String
    let exerciseSetId: String
    
    @State private var isEditing = false
    @State private var pendingValue = ""
    @State private var selectedUnit: DistanceUnit = .mile
    @FocusState private var isFocused: Bool
    
    private var displayValue: String {
        if let distance = distance {
            return "\(distance.value.formatted()) \(distance.unit.rawValue)"
        }
        return "-- mi"
    }
    
    var body: some View {
        if isEditing {
            HStack(spacing: 2) {
                TextField("0", text: $pendingValue)
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.center)
                    .font(Typography.body)
                    .fontWeight(.medium)
                    .focused($isFocused)
                    .frame(width: 50)
                
                Menu {
                    ForEach([DistanceUnit.mile, .kilometer, .meter, .yard], id: \.self) { unit in
                        Button(unit.rawValue) {
                            selectedUnit = unit
                        }
                    }
                } label: {
                    Text(selectedUnit.rawValue)
                        .font(Typography.caption1)
                        .foregroundColor(Colors.primary)
                }
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(Colors.primary.opacity(0.1))
            .cornerRadius(Radii.small)
            .onAppear {
                pendingValue = distance?.value.formatted() ?? ""
                selectedUnit = distance?.unit ?? .mile
                isFocused = true
            }
            .onChange(of: isFocused) { _, focused in
                if !focused { save() }
            }
        } else {
            Button(action: { isEditing = true }) {
                Text(displayValue)
                    .font(Typography.body)
                    .fontWeight(.medium)
                    .foregroundColor(distance == nil ? Colors.onSurface.opacity(0.3) :
                                   (isComplete ? Colors.onSurface.opacity(0.5) : Colors.onSurface))
                    .frame(maxWidth: .infinity)
                    .monospacedDigit()
            }
            .buttonStyle(PlainButtonStyle())
        }
    }
    
    private func save() {
        isEditing = false
        guard let value = Double(pendingValue), value >= 0 else { return }
    }
}

#Preview {
    DistanceInputView(
        distance: Distance(value: 1, unit: .mile),
        isComplete: false,
        exerciseId: "id",
        exerciseSetId: "setid"
    )
}
