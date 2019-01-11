// Test to verify dns record created for instances created by autoscaling group

package test

import (
	"fmt"
	"strings"
	"testing"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/awserr"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/route53"
	a "github.com/gruntwork-io/terratest/modules/aws"
	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

//Get instanceId,HostedZoneName and verify dns record using terratest and aws-sdk-go modules

func TestAwsDnsRecordName(t *testing.T) {
	awsRegion := "eu-west-1"

	//Specify the path where Terraform code to be tested is loacated
	terraformOptions := &terraform.Options{
		TerraformDir: "../../example/asg-dns-agent",
	}

	// At the end of the test, run `terraform destroy` to clean up any resources that were created
	defer terraform.Destroy(t, terraformOptions)

	//This will run `terraform init` and `terraform apply` and fail the test if there are any errors
	terraform.InitAndApply(t, terraformOptions)

	//Get instanceIDs that were created by the autoscaling group
	asgName := terraform.Output(t, terraformOptions, "asg_name")
	instanceIds := a.GetInstanceIdsForAsg(t, asgName, awsRegion)

	//Look up the tags for the given Instance ID
	instanceTags := a.GetTagsForEc2Instance(t, awsRegion, instanceIds[0])

	//Get the name of the instance
	nameTag, containsNameTag := instanceTags["Name"]
	assert.True(t, containsNameTag)

	//Get the dns hosted zone name
	dnsHostedZoneName := terraform.Output(t, terraformOptions, "vpc_internal_dns_name")
	dnsHostedZoneId := terraform.Output(t, terraformOptions, "vpc_internal_dns_id")
	//Concatenate the instance name and the hosted zone name to get the Dns record name, which will be passed on to ListResourceRecordSetsInput as an input parameter
	name := &nameTag
	zoneName := &dnsHostedZoneName
	s := []string{*name, *zoneName}
	recordName := strings.Join(s, ".")
	recordNamePointer := &recordName
	fmt.Println(*recordNamePointer)

	ZoneId := &dnsHostedZoneId
	//Connect to route53 and verify the dns record exits
	svc := route53.New(session.New())

	input := &route53.ListResourceRecordSetsInput{
		HostedZoneId:    aws.String(*ZoneId),
		MaxItems:        aws.String("1"),
		StartRecordName: aws.String(*recordNamePointer),
		StartRecordType: aws.String("A"),
	}

	res, err := svc.ListResourceRecordSets(input)
	if err != nil {
		if aerr, ok := err.(awserr.Error); ok {
			switch aerr.Code() {
			case route53.ErrCodeNoSuchHostedZone:
				fmt.Println(route53.ErrCodeNoSuchHostedZone, aerr.Error())
			case route53.ErrCodeInvalidInput:
				fmt.Println(route53.ErrCodeInvalidInput, aerr.Error())
			default:
				fmt.Println(aerr.Error())
			}
		} else {
			fmt.Println(err.Error())
		}
		return
	}
	fmt.Println(res)
}
