module abs_diff_i724_o362(a,b,r);
input [361:0] a,b;
output [361:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
