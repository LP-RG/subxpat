module abs_diff_i940_o470(a,b,r);
input [469:0] a,b;
output [469:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
