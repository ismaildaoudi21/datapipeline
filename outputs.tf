################################################################################
# Client Machine (EC2 instance)
################################################################################
output "execute_this_to_access_the_bastion_host" {
  value = "ssh ec2-user@${aws_instance.bastion_host.public_ip} -i cert.pem"
}
output "msk_bootstrap_brokers" {
  value = aws_msk_cluster.kafka.bootstrap_brokers
}