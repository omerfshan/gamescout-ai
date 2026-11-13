<?php
declare(strict_types=1);
namespace App\Infrastructure\Auth;
use App\Domain\Auth\{AuthenticatedUser, AuthSession, InvalidCredentials, UserAuthenticator};
use App\Models\User;
use Illuminate\Support\Facades\{DB, Hash};
final class SanctumUserAuthenticator implements UserAuthenticator
{
    public function login(string $email, string $password, string $deviceName): AuthSession
    {
        /** @var User|null $user */
        $user = User::query()->where('email', $email)->first();
        if ($user === null || !Hash::check($password, (string) $user->password)) {
            throw new InvalidCredentials('E-posta veya parola hatalı.');
        }
        $token = $user->createToken($deviceName)->plainTextToken;
        return new AuthSession(
            new AuthenticatedUser((int) $user->getKey(), (string) $user->name, (string) $user->email),
            $token
        );
    }
    public function logout(int $userId, ?int $accessTokenId): void
    {
        $query = DB::table('personal_access_tokens')
            ->where('tokenable_type', User::class)
            ->where('tokenable_id', $userId);
        if ($accessTokenId !== null) {
            $query->where('id', $accessTokenId);
        }
        $query->delete();
    }
}
