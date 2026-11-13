<?php
declare(strict_types=1);
namespace App\Domain\Auth;
final readonly class AuthenticatedUser
{
    public function __construct(public int $id, public string $name, public string $email)
    {
        if ($id <= 0 || trim($name) === '' || trim($email) === '') {
            throw new \InvalidArgumentException('Geçersiz kullanıcı kimliği.');
        }
    }
    public function toArray(): array
    {
        return ['id' => $this->id, 'name' => $this->name, 'email' => $this->email];
    }
}
