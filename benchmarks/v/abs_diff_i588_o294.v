module abs_diff_i588_o294(a,b,r);
input [293:0] a,b;
output [293:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
