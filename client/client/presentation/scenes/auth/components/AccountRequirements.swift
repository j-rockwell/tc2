import SwiftUI
import Combine

struct AccountRequirements: View {
    let username: String
    let email: String
    let password: String
    let confirmPassword: String
    
    @StateObject private var lookup = AvailabilityLookup()
    @State private var animationOffset: CGFloat = 15
    @State private var animationOpacity: Double = 0
    @State private var checkmarkScale: CGFloat = 0.1
    
    private var isValidUsernameFormat: Bool {
        return false
    }
    
    private var isValidEmailFormat: Bool {
        return false
    }
    
    var isValidUsername: Bool {
        username.count >= 3 && username.count <= 16 &&
        isValidUsernameFormat &&
        lookup.isUsernameAvailable
    }
    
    var isValidEmail: Bool {
        isValidEmailFormat &&
        lookup.isEmailAvailable
    }
    
    var isValidPassword: Bool {
        password.count > 6 && password.count <= 32 &&
        password == confirmPassword &&
        !confirmPassword.isEmpty
    }
    
    var ok: Bool {
        return isValidUsername && isValidEmail && isValidPassword
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.xl2) {
            // Username section
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Text("Username:")
                        .fontWeight(.medium)
                    
                    AnimatedCheckmark(isValid: true, isChecking: lookup.isCheckingUsername)
                        .scaleEffect(checkmarkScale)
                        .animation(.spring(response: 0.5, dampingFraction: 0.7), value: checkmarkScale)
                    
                    Spacer()
                }
                .offset(x: animationOffset)
                .opacity(animationOpacity)
                .animation(.easeOut(duration: 0.4).delay(0.1), value: animationOffset)
                
                Text("Usernames must be a-z 0-9 and 2-16 characters in length")
                    .font(.caption)
                    .offset(x: animationOffset)
                    .opacity(animationOpacity)
                    .animation(.easeOut(duration: 0.4).delay(0.15), value: animationOffset)
            }
            
            // Email section
            HStack(spacing: 8) {
                Text("Email:")
                    .fontWeight(.medium)
                
                AnimatedCheckmark(isValid: true, isChecking: lookup.isCheckingEmail)
                    .scaleEffect(checkmarkScale)
                    .animation(.spring(response: 0.5, dampingFraction: 0.7), value: checkmarkScale)
                
                Spacer()
            }
            .offset(x: animationOffset)
            .opacity(animationOpacity)
            .animation(.easeOut(duration: 0.4).delay(0.2), value: animationOffset)
            
            // Password section
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Text("Password:")
                        .fontWeight(.medium)
                    
                    AnimatedCheckmark(isValid: true, isChecking: false)
                        .scaleEffect(checkmarkScale)
                        .animation(.spring(response: 0.5, dampingFraction: 0.7), value: checkmarkScale)
                    
                    Spacer()
                }
                .offset(x: animationOffset)
                .opacity(animationOpacity)
                .animation(.easeOut(duration: 0.4).delay(0.25), value: animationOffset)
                
                Text("Passwords must be 6-32 characters")
                    .font(.caption)
                    .offset(x: animationOffset)
                    .opacity(animationOpacity)
                    .animation(.easeOut(duration: 0.4).delay(0.3), value: animationOffset)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 0)
        .ignoresSafeArea(.container, edges: .horizontal)
        .onAppear {
            // Trigger entrance animations
            withAnimation {
                animationOffset = 0
                animationOpacity = 1
                checkmarkScale = 1.0
            }
        }
    }
}

struct AnimatedCheckmark: View {
    let isValid: Bool
    let isChecking: Bool
    
    @State private var rotationAngle: Double = 0
    @State private var checkmarkScale: CGFloat = 1.0
    @State private var showCheckmark: Bool = false
    
    var body: some View {
        ZStack {
            if isChecking {
                // Loading spinner
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(Color.primary, lineWidth: 2)
                    .frame(width: 16, height: 16)
                    .rotationEffect(.degrees(rotationAngle))
                    .onAppear {
                        withAnimation(.linear(duration: 1.0).repeatForever(autoreverses: false)) {
                            rotationAngle = 360
                        }
                    }
                    .onDisappear {
                        rotationAngle = 0
                    }
            } else if isValid {
                // Animated checkmark
                Text("✅")
                    .font(.system(size: 16))
                    .scaleEffect(checkmarkScale)
                    .opacity(showCheckmark ? 1 : 0)
                    .onAppear {
                        withAnimation(.spring(response: 0.6, dampingFraction: 0.8).delay(0.1)) {
                            showCheckmark = true
                            checkmarkScale = 1.2
                        }
                        
                        // Bounce back to normal size
                        withAnimation(.spring(response: 0.4, dampingFraction: 0.8).delay(0.3)) {
                            checkmarkScale = 1.0
                        }
                    }
            } else {
                // Invalid state
                Text("❌")
                    .font(.system(size: 16))
                    .opacity(0.6)
            }
        }
    }
}

class AvailabilityLookup: ObservableObject {
    @Published var isUsernameAvailable = false
    @Published var isEmailAvailable = false
    @Published var isCheckingUsername = false
    @Published var isCheckingEmail = false
    
    private var usernameCancellable: AnyCancellable?
    private var emailCancellable: AnyCancellable?
    private var networkService: NetworkServiceProtocol
    
    init(networkService: NetworkServiceProtocol = NetworkService()) {
        self.networkService = networkService
    }
    
    func checkUsernme(_ username: String) {
        guard (username.count > 2) else {
            isUsernameAvailable = false
            return
        }
        
        usernameCancellable?.cancel()
        isCheckingUsername = true
        
        usernameCancellable = Just(username)
                    .delay(for: .milliseconds(500), scheduler: DispatchQueue.main)
                    .flatMap { [weak self] username -> AnyPublisher<Bool, Never> in
                        guard let self = self else {
                            return Just(false).eraseToAnyPublisher()
                        }
                        
                        return self.networkService
                            .request(CheckUsernameAvailabilityRequest(username: username))
                            .map { response in
                                response.response
                            }
                            .catch { _ in
                                Just(false)
                            }
                            .eraseToAnyPublisher()
                    }
                    .receive(on: DispatchQueue.main)
                    .sink { [weak self] isAvailable in
                        self?.isUsernameAvailable = isAvailable
                        self?.isCheckingUsername = false
                    }
    }
    
    func checkEmail(_ email: String) {
        
    }
}

#Preview {
    AccountRequirements(username: "kcor.j", email: "john@test.com", password: "password123", confirmPassword: "password123")
}
