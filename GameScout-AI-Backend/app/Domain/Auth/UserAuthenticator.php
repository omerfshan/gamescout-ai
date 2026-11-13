<?php
declare(strict_types=1);
namespace App\Domain\Auth;
interface UserAuthenticator
{
    public function login(string $email, string $password, string $deviceName): AuthSession;
    public function logout(int $userId, ?int $accessTokenId): void;
}
