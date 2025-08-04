import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    
    private var name: String {
        guard let account = authManager.account else { return "Guest" }
        return account.username
    }
    
    var body: some View {
        VStack {
            DashboardGreeting(name: name)
            Spacer()
            Text("Dashboard View")
            Spacer()
        }
        .padding()
    }
}

struct DashboardGreeting: View {
    let name: String
    
    private var salutation: String {
        let hour = Calendar.current.component(.hour, from: Date())
        
        switch hour {
        case 5..<12:
            return "Good morning"
        case 12..<17:
            return "Good afternoon"
        case 17..<24:
            return "Good evening"
        default:
            return "Hello"
        }
    }
    
    var body: some View {
        Text("\(salutation), \(name)")
            .font(Typography.title1)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    let mockAuthManager = AuthenticationManager()
    mockAuthManager.isAuthenticated = true
    mockAuthManager.account = Account(
        id: "123",
        username: "testuser",
        email: "test@trainingclub.com",
        profile: AccountProfile(name: "Test User", avatar: nil),
        bio: nil,
        metadata: nil,
    )
    
    return DashboardView()
        .environmentObject(mockAuthManager)
}
