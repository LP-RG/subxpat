module abs_diff_i32768_o16384(a,b,r);
input [16383:0] a,b;
output [16383:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
