import SwiftUI

struct NewSessionView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    var body: some View {
        VStack {
            PageTitleView(title: "Start Session")
            VStack {
                HStack {
                    NewSessionItemView(label: "Blank", description:"Create an empty session", action: handleCreateBlankSession)
                    NewSessionItemView(label: "Group", description:"Share a session with others", action: handleCreateGroupSession)
                }
            }
            Spacer()
        }
    }
    
    private func handleCreateBlankSession() {
        print("handleCreateBlankSession")
    }
    
    private func handleCreateGroupSession() {
        Task {
            await exerciseSessionManager.createSession()
        }
    }
}

struct NewSessionItemView: View {
    var label: String
    var description: String?
    var action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                VStack {
                    Text(label)
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .foregroundColor(Colors.onSurface)
                    if description != nil {
                        Text(description!)
                            .font(Typography.caption2)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .foregroundColor(Colors.onSurface)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxWidth: .infinity)
            .padding(.horizontal, Spacing.sm)
            .padding(.vertical, Spacing.md)
            .background(Colors.surface)
            .cornerRadius(Radii.small)
        }
    }
}

#Preview {
    NewSessionView()
        .environmentObject(ExerciseSessionManager())
}
