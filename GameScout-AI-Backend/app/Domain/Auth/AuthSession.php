<?php
declare(strict_types=1);
namespace App\Domain\Auth;
final readonly class AuthSession
{
    public function __construct(public AuthenticatedUser $user, public string $token)
    {
        if (trim($token) === '') {
            throw new \InvalidArgumentException('Boş oturum anahtarı.');
        }
    }
    public function toArray(): array
    {
        return ['user' => $this->user->toArray(), 'token' => $this->token, 'token_type' => 'Bearer'];
    }
}
