module abs_diff_i908_o454(a,b,r);
input [453:0] a,b;
output [453:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
