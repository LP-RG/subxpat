module abs_diff_i92_o46(a,b,r);
input [45:0] a,b;
output [45:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
