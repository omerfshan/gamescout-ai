<?php
declare(strict_types=1);
namespace App\Application\Auth;
use App\Domain\Auth\AuthenticatedUser;
final readonly class GetAuthenticatedUser
{
    public function execute(AuthenticatedUser $user): array
    {
        return $user->toArray();
    }
}
