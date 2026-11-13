<?php
declare(strict_types=1);
namespace App\Application\Auth;
use App\Domain\Auth\UserAuthenticator;
final readonly class LoginUser
{
    public function __construct(private UserAuthenticator $authenticator) {}
    public function execute(string $email, string $password, string $deviceName = 'dashboard'): array
    {
        $normalizedEmail = strtolower(trim($email));
        $normalizedDevice = trim($deviceName) !== '' ? trim($deviceName) : 'dashboard';
        return $this->authenticator->login($normalizedEmail, $password, $normalizedDevice)->toArray();
    }
}
