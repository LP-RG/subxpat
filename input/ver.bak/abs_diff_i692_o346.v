module abs_diff_i692_o346(a,b,r);
input [345:0] a,b;
output [345:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
