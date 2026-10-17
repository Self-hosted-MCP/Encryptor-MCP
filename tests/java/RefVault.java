// SPDX-License-Identifier: AGPL-3.0-only
// The reference: Cryptomator's own libraries (cryptofs and cryptolib, from Cryptomator.app) make test vaults and
// read vaults back, so Encryptor-MCP's results can be checked against the official code in both directions.
//
//   java -cp "<Cryptomator.app>/Contents/app/mods/*" RefVault.java make <vaultDir> <SIV_GCM|SIV_CTRMAC> <password>
//   java -cp ... RefVault.java dump <vaultDir> <password>          (one line per entry: type, path, size, sha256)
//   java -cp ... RefVault.java write <vaultDir> <password> <path> <text>
//   java -cp ... RefVault.java health <vaultDir> <password>          (Cryptomator's own health check: one line per problem)
//   java -cp ... RefVault.java recoverykey <vaultDir> <password>     (needs Cryptomator.app's own jar)
//   java -cp ... RefVault.java resetpw <vaultDir> <recoveryKey> <newPassword>
import org.cryptomator.cryptofs.CryptoFileSystemProperties;
import org.cryptomator.cryptofs.CryptoFileSystemProvider;
import org.cryptomator.cryptolib.api.CryptorProvider;
import org.cryptomator.cryptolib.api.Masterkey;
import org.cryptomator.cryptolib.api.MasterkeyLoader;
import org.cryptomator.cryptolib.common.MasterkeyFileAccess;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.stream.Stream;

public class RefVault {
    static final SecureRandom RNG = new SecureRandom();

    static CryptoFileSystemProperties props(Path vault, String password, CryptorProvider.Scheme scheme) {
        MasterkeyFileAccess mfa = new MasterkeyFileAccess(new byte[0], RNG);
        MasterkeyLoader loader = uri -> {
            try { return mfa.load(vault.resolve("masterkey.cryptomator"), password); }
            catch (Exception e) { throw new RuntimeException(e); }
        };
        var b = CryptoFileSystemProperties.cryptoFileSystemProperties().withKeyLoader(loader);
        if (scheme != null) b = b.withCipherCombo(scheme);
        return b.build();
    }

    // Arguments may come as "b64:<base64 of UTF-8>", so names outside the system code page (Windows) arrive intact.
    static String arg(String a) {
        return a.startsWith("b64:") ? new String(java.util.Base64.getDecoder().decode(a.substring(4)), StandardCharsets.UTF_8) : a;
    }

    static Class<?> recoveryFactory() throws Exception {
        return Class.forName("org.cryptomator.ui.recoverykey.RecoveryKeyFactory");
    }

    static Object factory() throws Exception {
        var enc = Class.forName("org.cryptomator.ui.recoverykey.WordEncoder").getDeclaredConstructor();
        enc.setAccessible(true);
        var ctor = recoveryFactory().getConstructors()[0];
        return ctor.newInstance(enc.newInstance(), new MasterkeyFileAccess(new byte[0], RNG));
    }

    public static void main(String[] raw) throws Exception {
        String[] args = java.util.Arrays.stream(raw).map(RefVault::arg).toArray(String[]::new);
        System.setOut(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), true, StandardCharsets.UTF_8));
        Path vault = Paths.get(args[1]);
        switch (args[0]) {
            case "make" -> {
                Files.createDirectories(vault);
                String password = args[3];
                Masterkey mk = Masterkey.generate(RNG);
                new MasterkeyFileAccess(new byte[0], RNG).persist(mk, vault.resolve("masterkey.cryptomator"), password);
                var p = props(vault, password, CryptorProvider.Scheme.valueOf(args[2]));
                CryptoFileSystemProvider.initialize(vault, p, URI.create("masterkeyfile:masterkey.cryptomator"));
                try (FileSystem fs = CryptoFileSystemProvider.newFileSystem(vault, p)) {
                    Files.writeString(fs.getPath("/hello.txt"), "Hello from Cryptomator's own code.\n");
                    Files.write(fs.getPath("/empty.txt"), new byte[0]);
                    byte[] big = new byte[100_000];
                    for (int i = 0; i < big.length; i++) big[i] = (byte) (i * 31 + 7);
                    Files.write(fs.getPath("/big.bin"), big);
                    Files.createDirectories(fs.getPath("/Folder A/Sub folder"));
                    Files.writeString(fs.getPath("/Folder A/Sub folder/notes ü é 日本.txt"), "Unicode name and text: ü é 日本\n");
                    String longName = "a very long file name " + "x".repeat(140) + ".txt";
                    Files.writeString(fs.getPath("/Folder A/" + longName), "This name is long enough to be shortened.\n");
                    Files.createDirectories(fs.getPath("/" + "Long folder name " + "y".repeat(140)));
                    Files.writeString(fs.getPath("/" + "Long folder name " + "y".repeat(140) + "/inside.txt"), "Inside a long folder.\n");
                    Files.createSymbolicLink(fs.getPath("/link to hello"), fs.getPath("hello.txt"));
                }
                System.out.println("made " + vault);
            }
            case "dump" -> {
                var p = props(vault, args[2], null);
                try (FileSystem fs = CryptoFileSystemProvider.newFileSystem(vault, p);
                     Stream<Path> all = Files.walk(fs.getPath("/"))) {
                    all.sorted().forEach(path -> {
                        try {
                            if (path.toString().equals("/")) return;
                            if (Files.isSymbolicLink(path)) {
                                System.out.println("link\t" + path + "\t" + Files.readSymbolicLink(path));
                            } else if (Files.isDirectory(path)) {
                                System.out.println("dir\t" + path);
                            } else {
                                byte[] data = Files.readAllBytes(path);
                                String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
                                System.out.println("file\t" + path + "\t" + data.length + "\t" + sha);
                            }
                        } catch (Exception e) { throw new RuntimeException(e); }
                    });
                }
            }
            case "write" -> {
                var p = props(vault, args[2], null);
                try (FileSystem fs = CryptoFileSystemProvider.newFileSystem(vault, p)) {
                    Files.writeString(fs.getPath(args[3]), args[4], StandardCharsets.UTF_8);
                }
                System.out.println("wrote " + args[3]);
            }
            case "health" -> {
                // Cryptomator's own health checks; prints one line per problem: severity, kind, details
                String password = args[2];
                Masterkey mk = new MasterkeyFileAccess(new byte[0], RNG).load(vault.resolve("masterkey.cryptomator"), password);
                var unverified = org.cryptomator.cryptofs.VaultConfig.decode(Files.readString(vault.resolve("vault.cryptomator")));
                var config = unverified.verify(mk.getEncoded(), 8);
                var cryptor = CryptorProvider.forScheme(config.getCipherCombo()).provide(mk.copy(), RNG);
                for (var check : org.cryptomator.cryptofs.health.api.HealthCheck.allChecks()) {
                    check.check(vault, config, mk, cryptor, r -> {
                        String sev = r.getSeverity().toString();
                        if (!sev.equals("GOOD")) {
                            System.out.println("problem\t" + sev + "\t" + r.getClass().getSimpleName() + "\t" + r.details());
                        }
                    });
                }
            }
            case "recoverykey" -> {
                // Cryptomator's own recovery key for a vault (its desktop app's RecoveryKeyFactory)
                System.out.println("key\t" + recoveryFactory().getMethod("createRecoveryKey", Path.class, CharSequence.class)
                        .invoke(factory(), vault, args[2]));
            }
            case "resetpw" -> {
                // Cryptomator's own "reset password with the recovery key"
                Object f = factory();
                boolean ok = (boolean) recoveryFactory().getMethod("validateRecoveryKey", String.class).invoke(f, args[2]);
                if (!ok) throw new IllegalArgumentException("Cryptomator says: not a valid recovery key");
                recoveryFactory().getMethod("newMasterkeyFileWithPassphrase", Path.class, String.class, CharSequence.class)
                        .invoke(f, vault, args[2], args[3]);
                System.out.println("reset\tok");
            }
            default -> throw new IllegalArgumentException("make | dump | write | health | recoverykey | resetpw");
        }
    }
}
