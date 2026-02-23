module abs_diff_i396_o198(a,b,r);
input [197:0] a,b;
output [197:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
