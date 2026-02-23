module abs_diff_i392_o196(a,b,r);
input [195:0] a,b;
output [195:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
