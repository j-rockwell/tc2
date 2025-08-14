import SwiftUI

struct WeightInputView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    let weight: Weight?
    let isComplete: Bool
    let exerciseId: String
    let exerciseSetId: String
    
    @State private var isEditing = false
    @State private var pendingValue = ""
    @State private var selectedUnit: WeightUnit = .pound
    @FocusState private var isFocused: Bool
    
    private var displayValue: String {
        if let weight = weight {
            return "\(weight.value.formatted()) \(weight.unit.rawValue)"
        }
        return "0"
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
                    ForEach([WeightUnit.pound, .kilogram], id: \.self) { unit in
                        Button(action: { selectedUnit = unit }) {
                            HStack {
                                Text(unit.rawValue)
                                if unit == selectedUnit {
                                    Spacer()
                                    Image(systemName: "checkmark")
                                }
                            }
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
                pendingValue = weight?.value.formatted() ?? ""
                selectedUnit = weight?.unit ?? .pound
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
                    .foregroundColor(weight == nil ? Colors.onSurface.opacity(0.3) :
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
    WeightInputView(
        weight: Weight(value: 135.0, unit: .pound),
        isComplete: false,
        exerciseId: "id",
        exerciseSetId: "set-id"
    )
}
