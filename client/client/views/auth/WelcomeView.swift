import SwiftUI

struct WelcomeView: View {
    var body: some View {
        WelcomeContentView(
            onCreateAccountPress: {
                print("onCreateAccountPress")
            },
            
            onSignInPress: {
                print("onSignInPress")
            }
        )
    }
}

private struct WelcomeContentView: View {
    let onCreateAccountPress: () -> Void
    let onSignInPress: () -> Void
    
    var body: some View {
        WelcomeButtons(onCreateAccountPress: onCreateAccountPress, onSignInPress: onSignInPress)
    }
}

private struct WelcomeButtons: View {
    let onCreateAccountPress: () -> Void
    let onSignInPress: () -> Void
    
    var body: some View {
        VStack() {
            Button(action: onSignInPress) {
                Text("Sign In")
            }
            .primary()
            
            Button(action: onCreateAccountPress) {
                Text("Create Account")
            }
            .primary()
        }
    }
}

#Preview {
    WelcomeView()
}
