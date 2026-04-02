module abs_diff_i800_o400(a,b,r);
input [399:0] a,b;
output [399:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
