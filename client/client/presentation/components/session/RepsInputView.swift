import SwiftUI

struct RepsInputView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    let reps: Int?
    let isComplete: Bool
    let exerciseId: String
    let exerciseSetId: String
    
    @State private var isEditing = false
    @State private var pendingValue = ""
    @FocusState private var isFocused: Bool
    
    var body: some View {
        if isEditing {
            TextField("0", text: $pendingValue)
                .keyboardType(.numberPad)
                .multilineTextAlignment(.center)
                .font(Typography.body)
                .fontWeight(.medium)
                .focused($isFocused)
                .frame(width: 50)
                .padding(.horizontal, 8)
                .padding(.vertical, 2)
                .background(Colors.primary.opacity(0.1))
                .cornerRadius(Radii.small)
                .onAppear {
                    pendingValue = reps?.description ?? ""
                    isFocused = true
                }
                .onChange(of: isFocused) { _, focused in
                    if !focused { save() }
                }
        } else {
            Button(action: { isEditing = true }) {
                Text(reps?.description ?? "--")
                    .font(Typography.body)
                    .fontWeight(.medium)
                    .foregroundColor(reps == nil ? Colors.onSurface.opacity(0.3) :
                                   (isComplete ? Colors.onSurface.opacity(0.5) : Colors.onSurface))
                    .frame(maxWidth: .infinity)
                    .monospacedDigit()
            }
            .buttonStyle(PlainButtonStyle())
        }
    }
    
    private func save() {
        isEditing = false
        guard let value = Int(pendingValue), value >= 0 else { return }
        print("update metrics with \(value)")
    }
}
