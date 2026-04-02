module abs_diff_i928_o464(a,b,r);
input [463:0] a,b;
output [463:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
