<?php
declare(strict_types=1);
namespace App\Application\Auth;
use App\Domain\Auth\UserAuthenticator;
final readonly class LogoutUser
{
    public function __construct(private UserAuthenticator $authenticator) {}
    public function execute(int $userId, ?int $accessTokenId): void
    {
        $this->authenticator->logout($userId, $accessTokenId);
    }
}
